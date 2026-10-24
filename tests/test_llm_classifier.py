import pytest

from app.classifiers.llm_classifier import LLMClassifier
from app.schemas import Category, EmailIn

EMAIL = EmailIn(sender="a@b.com", subject="I want my money back", body="Item arrived damaged")


def test_parses_clean_json():
    clf = LLMClassifier(lambda s, u: '{"category": "Order Support", "confidence": 0.9, "reasoning": "return"}')
    r = clf.classify(EMAIL)
    assert r.category == Category.ORDER_SUPPORT and r.confidence == 0.9 and r.method == "llm"


def test_parses_json_wrapped_in_markdown():
    raw = '```json\n{"category": "Billing", "confidence": 0.8}\n```'
    assert LLMClassifier(lambda s, u: raw).classify(EMAIL).category == Category.BILLING


def test_unknown_category_falls_back_to_general():
    raw = '{"category": "Spam", "confidence": 0.7}'
    assert LLMClassifier(lambda s, u: raw).classify(EMAIL).category == Category.GENERAL


def test_confidence_is_clamped():
    raw = '{"category": "Billing", "confidence": 7}'
    assert LLMClassifier(lambda s, u: raw).classify(EMAIL).confidence == 1.0


def test_non_json_raises():
    with pytest.raises(ValueError):
        LLMClassifier(lambda s, u: "I think it is billing").classify(EMAIL)
