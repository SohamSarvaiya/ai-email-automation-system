"""Version 1: keyword/rule based classifier (no AI needed)."""
import re

from app.classifiers.base import BaseClassifier
from app.schemas import Category, ClassificationResult, EmailIn

KEYWORDS: dict[Category, list[str]] = {
    Category.ORDER_SUPPORT: [
        "order", "delayed", "delay", "delivery", "delivered", "shipped", "shipping",
        "tracking", "package", "parcel", "not received", "refund", "return", "cancel",
    ],
    Category.SALES_INQUIRY: [
        "price", "pricing", "quote", "quotation", "demo", "bulk", "discount",
        "buy", "purchase", "catalog", "interested", "plans", "enterprise",
    ],
    Category.TECHNICAL_SUPPORT: [
        "log in", "login", "sign in", "password", "error", "bug", "crash", "crashing",
        "not working", "cannot access", "reset", "2fa", "otp", "website down", "app",
    ],
    Category.BILLING: [
        "invoice", "bill", "billing", "payment", "charged", "receipt", "gst",
        "tax", "overcharged", "statement", "paid",
    ],
}

SUBJECT_WEIGHT = 2  # a keyword in the subject counts double


def _normalize(text: str) -> str:
    return text.lower().replace("’", "'").replace("can't", "cannot").replace("can not", "cannot")


def _count(text: str, words: list[str]) -> int:
    return sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", text))


class RuleBasedClassifier(BaseClassifier):
    name = "rules"

    def classify(self, email: EmailIn) -> ClassificationResult:
        subject, body = _normalize(email.subject), _normalize(email.body)
        scores: dict[Category, int] = {}
        for cat, words in KEYWORDS.items():
            scores[cat] = _count(subject, words) * SUBJECT_WEIGHT + _count(body, words)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        (top_cat, top), (_, second) = ranked[0], ranked[1]

        if top == 0:
            return ClassificationResult(
                category=Category.GENERAL, confidence=0.3, method=self.name,
                reasoning="No keyword matched",
            )
        confidence = round(top / (top + second + 1), 2)
        return ClassificationResult(
            category=top_cat, confidence=confidence, method=self.name,
            reasoning=f"Keyword score {top} (runner-up {second})",
        )
