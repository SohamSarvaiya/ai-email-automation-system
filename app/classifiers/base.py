from abc import ABC, abstractmethod

from app.schemas import ClassificationResult, EmailIn


class BaseClassifier(ABC):
    """Every classifier (rules, LLM, ...) implements this interface (OOP)."""

    name: str = "base"

    @abstractmethod
    def classify(self, email: EmailIn) -> ClassificationResult:
        ...
