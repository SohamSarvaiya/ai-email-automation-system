"""Creates a reply draft: template based by default, LLM based if available."""
from typing import Optional

from app.classifiers.llm_classifier import CompleteFn
from app.schemas import Category, EmailIn, ExtractedInfo

TEMPLATES = {
    Category.ORDER_SUPPORT: "Thank you for contacting us about your order{ref}. Our support team is checking the status and will update you within 24 hours.",
    Category.SALES_INQUIRY: "Thank you for your interest! Our sales team will share pricing and product details shortly. Could you tell us your expected quantity and timeline?",
    Category.TECHNICAL_SUPPORT: "Sorry you are facing this issue. Our IT team has been notified. Meanwhile, please try resetting your password or clearing your cache and let us know if the problem continues.",
    Category.BILLING: "Thank you for reaching out about billing{ref}. Our finance team will review your request and send the required documents within 1-2 business days.",
    Category.GENERAL: "Thank you for your email. We have received it and a team member will get back to you soon.",
}

DRAFT_SYSTEM = ("You write short, polite, professional customer-support email replies. "
                "Do not invent facts, prices or deadlines. Output only the email body.")


def _name(sender: str) -> str:
    local = sender.split("@")[0].replace(".", " ").replace("_", " ").strip()
    return local.title() or "there"


class ReplyDrafter:
    def __init__(self, complete: Optional[CompleteFn] = None):
        self._complete = complete

    def draft(self, email: EmailIn, category: Category, info: ExtractedInfo) -> str:
        if self._complete:
            try:
                prompt = (f"Category: {category.value}\nExtracted info: {info.model_dump_json()}\n"
                          f"Customer email:\nSubject: {email.subject}\n{email.body}\n\nWrite the reply.")
                return self._complete(DRAFT_SYSTEM, prompt).strip()
            except Exception:
                pass  # fall back to template
        ref = ""
        if info.order_ids:
            ref = f" ({info.order_ids[0]})"
        elif info.invoice_numbers:
            ref = f" ({info.invoice_numbers[0]})"
        return f"Hi {_name(email.sender)},\n\n{TEMPLATES[category].format(ref=ref)}\n\nBest regards,\nCustomer Care Team"
