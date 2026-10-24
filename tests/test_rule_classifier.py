import pytest

from app.classifiers.rule_based import RuleBasedClassifier
from app.schemas import Category, EmailIn

clf = RuleBasedClassifier()


@pytest.mark.parametrize("subject,body,expected", [
    ("My order is delayed", "Where is my delivery?", Category.ORDER_SUPPORT),
    ("Need product pricing", "Please share a quote", Category.SALES_INQUIRY),
    ("Cannot log in", "Password reset not working", Category.TECHNICAL_SUPPORT),
    ("Please send invoice", "Need the GST bill", Category.BILLING),
    ("Hello", "Thanks for everything", Category.GENERAL),
])
def test_basic_categories(subject, body, expected):
    result = clf.classify(EmailIn(sender="a@b.com", subject=subject, body=body))
    assert result.category == expected
    assert result.method == "rules"


def test_apostrophe_variant_matches_cannot():
    r = clf.classify(EmailIn(sender="a@b.com", subject="Help", body="I can’t log in at all"))
    assert r.category == Category.TECHNICAL_SUPPORT


def test_no_match_gives_low_confidence():
    r = clf.classify(EmailIn(sender="a@b.com", subject="Hi", body="Nice weather"))
    assert r.category == Category.GENERAL and r.confidence < 0.45


def test_subject_counts_more_than_body():
    r = clf.classify(EmailIn(sender="a@b.com", subject="Invoice needed", body="order order"))
    assert r.category == Category.BILLING
