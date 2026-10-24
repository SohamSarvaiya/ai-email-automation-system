"""FastAPI application. Run: uvicorn app.main:app --reload"""
import logging
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query

from app.classifiers.llm_classifier import LLMClassifier, make_anthropic_complete
from app.classifiers.rule_based import RuleBasedClassifier
from app.config import Settings
from app.database import Database
from app.drafter import ReplyDrafter
from app.schemas import EmailIn, ProcessedEmail
from app.service import EmailProcessor, LLMNotConfigured

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(settings: Optional[Settings] = None, llm_complete=None) -> FastAPI:
    """App factory. `llm_complete` lets tests inject a fake LLM."""
    settings = settings or Settings.from_env()
    if llm_complete is None and settings.anthropic_api_key:
        llm_complete = make_anthropic_complete(settings.anthropic_api_key, settings.llm_model)

    db = Database(settings.database_path)
    processor = EmailProcessor(
        db=db, rules=RuleBasedClassifier(),
        llm=LLMClassifier(llm_complete) if llm_complete else None,
        drafter=ReplyDrafter(llm_complete), review_threshold=settings.review_threshold,
    )

    app = FastAPI(title="AI Email Automation System", version="1.0.0",
                  description="Classify, extract, route and draft replies for incoming emails.")

    @app.get("/health")
    def health():
        return {"status": "ok", "llm_enabled": processor.llm is not None}

    @app.post("/emails/process", response_model=ProcessedEmail)
    def process_email(email: EmailIn,
                      method: Literal["rules", "llm", "both"] = Query("rules")):
        try:
            return processor.process(email, method)
        except LLMNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    @app.get("/emails")
    def list_emails(limit: int = Query(50, le=500), category: Optional[str] = None):
        return db.list_emails(limit, category)

    @app.get("/emails/{email_id}", response_model=ProcessedEmail)
    def get_email(email_id: int):
        result = db.get_email(email_id)
        if not result:
            raise HTTPException(status_code=404, detail="Email not found")
        return result

    @app.get("/logs")
    def logs(limit: int = Query(100, le=1000)):
        return db.list_logs(limit)

    return app


app = create_app()
