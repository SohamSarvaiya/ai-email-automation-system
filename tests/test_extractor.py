from app.extractor import extract_info
from app.schemas import EmailIn


def mk(body, subject="s"):
    return EmailIn(sender="a@b.com", subject=subject, body=body)


def test_order_id_prefix():
    assert extract_info(mk("My order ORD-48213 is late")).order_ids == ["ORD-48213"]


def test_order_hash():
    assert extract_info(mk("Order #77120 not updating")).order_ids == ["77120"]


def test_invoice_and_amount():
    info = extract_info(mk("Send invoice INV-2024-0099 for Rs. 12,500"))
    assert info.invoice_numbers == ["INV-2024-0099"]
    assert info.amounts == ["12,500"]


def test_phone_and_email():
    info = extract_info(mk("Call +91 98765 43210 or mail me at x@y.com"))
    assert info.phones and info.emails == ["x@y.com"]


def test_urgent_flag():
    assert extract_info(mk("Please fix ASAP")).urgent is True
    assert extract_info(mk("Whenever you can")).urgent is False


def test_plain_word_after_order_is_not_an_id():
    assert extract_info(mk("My order is delayed")).order_ids == []
