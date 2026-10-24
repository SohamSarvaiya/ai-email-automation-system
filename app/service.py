"""The pipeline: receive -> classify -> extract -> route -> draft -> log."""
import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from app.classifiers.llm_classifier import LLMClassifier
from app.classifiers.rule_based import RuleBasedClassifier
from app.database import Database
from app.drafter import ReplyDrafter
from app.extractor import extract_info
from app.schemas import DEPARTMENT_MAP, EmailIn, ProcessedEmail

logger = logging.getLogger("email_automation")
Method = Literal["rules", "llm", "both"]


class LLMNotConfigured(Exception):
    pass


class EmailProcessor:
    def __init__(self, db: Database, rules: RuleBasedClassifier,
                 llm: Optional[LLMClassifier], drafter: ReplyDrafter, review_threshold: float = 0.45):
        self.db, self.rules, self.llm = db, rules, llm
        self.drafter, self.review_threshold = drafter, review_threshold

    def process(self, email: EmailIn, method: Method = "rules") -> ProcessedEmail:
        if method in ("llm", "both") and self.llm is None:
            raise LLMNotConfigured("Set ANTHROPIC_API_KEY to use the LLM classifier")
        self.db.log("email_received", detail=f"{email.sender} | {email.subject}")

        rule_res = self.rules.classify(email) if method in ("rules", "both") else None
        llm_res = None
        if method in ("llm", "both"):
            try:
                llm_res = self.llm.classify(email)
            except Exception as exc:  # LLM down / bad JSON -> fall back to rules
                logger.warning("LLM failed, falling back to rules: %s", exc)
                self.db.log("llm_error", detail=str(exc))
                rule_res = rule_res or self.rules.classify(email)

        final = llm_res or rule_res
        agreement = (rule_res.category == llm_res.category) if (rule_res and llm_res) else None
        info = extract_info(email)
        draft = self.drafter.draft(email, final.category, info)

        result = ProcessedEmail(
            received_at=datetime.now(timezone.utc), email=email,
            rule_result=rule_res, llm_result=llm_res, final=final, agreement=agreement,
            department=DEPARTMENT_MAP[final.category],
            priority="high" if info.urgent else "normal",
            needs_human_review=final.confidence < self.review_threshold or agreement is False,
            extracted=info, draft_reply=draft,
        )
        result.id = self.db.save_email(result)
        self.db.log("email_processed", result.id,
                    f"{final.category.value} -> {result.department} ({final.method}, {final.confidence})")
        logger.info("Email %s classified as %s", result.id, final.category.value)
        return result
