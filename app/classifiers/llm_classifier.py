"""Version 2: LLM based classifier (Anthropic API)."""
import json
import re
from typing import Callable, Optional

from app.classifiers.base import BaseClassifier
from app.schemas import Category, ClassificationResult, EmailIn

# complete(system_prompt, user_prompt) -> raw text. Injectable so tests need no API key.
CompleteFn = Callable[[str, str], str]

SYSTEM_PROMPT = """You are an email triage assistant for a company.
Classify the email into exactly one category:
- Order Support: delivery, delays, tracking, returns, refunds, cancellations
- Sales Inquiry: pricing, quotes, demos, bulk purchases
- Technical Support: login problems, errors, bugs, product not working
- Billing: invoices, payments, charges, receipts, tax documents
- General: anything else
Respond with ONLY a JSON object:
{"category": "<one of the categories>", "confidence": <0.0-1.0>, "reasoning": "<one short sentence>"}"""


def make_anthropic_complete(api_key: str, model: str) -> CompleteFn:
    """Build a `complete` function backed by the Anthropic API."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    def complete(system: str, user: str) -> str:
        resp = client.messages.create(
            model=model, max_tokens=500, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text

    return complete


class LLMClassifier(BaseClassifier):
    name = "llm"

    def __init__(self, complete: CompleteFn):
        self._complete = complete

    def classify(self, email: EmailIn) -> ClassificationResult:
        user_prompt = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
        raw = self._complete(SYSTEM_PROMPT, user_prompt)
        return self.parse(raw)

    def parse(self, raw: str) -> ClassificationResult:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"LLM did not return JSON: {raw[:100]!r}")
        data = json.loads(match.group(0))
        try:
            category = Category(data["category"])
        except (KeyError, ValueError):
            category = Category.GENERAL
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        return ClassificationResult(
            category=category, confidence=confidence, method=self.name,
            reasoning=str(data.get("reasoning", "")),
        )
