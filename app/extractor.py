"""Pulls key information (order id, invoice no, amount, phone...) out of an email."""
import re

from app.schemas import EmailIn, ExtractedInfo

ORD_PREFIX = re.compile(r"\bORD-\d+\b", re.I)
ORDER_RE = re.compile(
    r"\border\s*(?:id|number|no\.?)?\s*[#:\-]?\s*(?=[A-Z0-9\-]*\d)([A-Z0-9\-]{4,})", re.I)
INVOICE_RE = re.compile(
    r"\b(?:invoice|inv)\s*(?:number|no\.?)?\s*[#:\-]?\s*(?=[A-Z0-9\-]*\d)([A-Z0-9\-]{3,})", re.I)
AMOUNT_RE = re.compile(r"(?:₹|rs\.?|inr|\$|usd)\s*([\d,]+(?:\.\d+)?)", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\d)(\+?\d[\d\s-]{8,14}\d)(?!\d)")
URGENT_WORDS = ("urgent", "asap", "immediately", "emergency", "critical", "right now")


def _unique(items):
    seen, out = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def extract_info(email: EmailIn) -> ExtractedInfo:
    text = f"{email.subject}\n{email.body}"
    orders = [m.upper() for m in ORD_PREFIX.findall(text)] or \
             [m.upper() for m in ORDER_RE.findall(text)]
    phones = [p.strip() for p in PHONE_RE.findall(text) if len(re.sub(r"\D", "", p)) >= 10]
    return ExtractedInfo(
        order_ids=_unique(orders),
        invoice_numbers=_unique(m.upper() for m in INVOICE_RE.findall(text)),
        amounts=_unique(AMOUNT_RE.findall(text)),
        emails=_unique(EMAIL_RE.findall(text)),
        phones=_unique(phones),
        urgent=any(w in text.lower() for w in URGENT_WORDS),
    )
