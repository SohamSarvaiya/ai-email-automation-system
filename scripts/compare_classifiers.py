"""Compare rule-based vs LLM classification on the labelled sample emails.

Usage:  python -m scripts.compare_classifiers
(LLM column is skipped automatically if ANTHROPIC_API_KEY is not set.)
"""
import json
from pathlib import Path

from app.classifiers.llm_classifier import LLMClassifier, make_anthropic_complete
from app.classifiers.rule_based import RuleBasedClassifier
from app.config import Settings
from app.schemas import EmailIn

SAMPLES = Path(__file__).resolve().parent.parent / "samples" / "sample_emails.json"


def main() -> None:
    settings = Settings.from_env()
    rules = RuleBasedClassifier()
    llm = (LLMClassifier(make_anthropic_complete(settings.anthropic_api_key, settings.llm_model))
           if settings.anthropic_api_key else None)

    data = json.loads(SAMPLES.read_text(encoding="utf-8"))
    rule_ok = llm_ok = 0
    print(f"{'Subject':38} {'Expected':18} {'Rules':18} {'LLM':18}")
    print("-" * 95)
    for row in data:
        email = EmailIn(sender=row["sender"], subject=row["subject"], body=row["body"])
        exp = row["expected_category"]
        r = rules.classify(email).category.value
        rule_ok += r == exp
        l = "(skipped)"
        if llm:
            l = llm.classify(email).category.value
            llm_ok += l == exp
        print(f"{row['subject'][:37]:38} {exp:18} {r:18}{'' if r == exp else ' X'} {l:18}{'' if (not llm or l == exp) else ' X'}")

    n = len(data)
    print("-" * 95)
    print(f"Rules accuracy: {rule_ok}/{n} = {rule_ok / n:.0%}")
    print(f"LLM accuracy  : {f'{llm_ok}/{n} = {llm_ok / n:.0%}' if llm else 'skipped (no API key)'}")


if __name__ == "__main__":
    main()
