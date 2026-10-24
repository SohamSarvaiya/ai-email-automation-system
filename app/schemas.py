"""Pydantic models (data contracts) used across the system."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    ORDER_SUPPORT = "Order Support"
    SALES_INQUIRY = "Sales Inquiry"
    TECHNICAL_SUPPORT = "Technical Support"
    BILLING = "Billing"
    GENERAL = "General"


# Category -> Department routing table
DEPARTMENT_MAP = {
    Category.ORDER_SUPPORT: "Support Team",
    Category.SALES_INQUIRY: "Sales Team",
    Category.TECHNICAL_SUPPORT: "IT Team",
    Category.BILLING: "Finance Team",
    Category.GENERAL: "Manual Review",
}


class EmailIn(BaseModel):
    sender: str = Field(..., examples=["rahul@example.com"])
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class ClassificationResult(BaseModel):
    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    method: str  # "rules" or "llm"
    reasoning: str = ""


class ExtractedInfo(BaseModel):
    order_ids: list[str] = []
    invoice_numbers: list[str] = []
    amounts: list[str] = []
    emails: list[str] = []
    phones: list[str] = []
    urgent: bool = False


class ProcessedEmail(BaseModel):
    id: Optional[int] = None
    received_at: datetime
    email: EmailIn
    rule_result: Optional[ClassificationResult] = None
    llm_result: Optional[ClassificationResult] = None
    final: ClassificationResult
    agreement: Optional[bool] = None  # rules vs llm, only when both ran
    department: str
    priority: str  # "high" | "normal"
    needs_human_review: bool
    extracted: ExtractedInfo
    draft_reply: str
