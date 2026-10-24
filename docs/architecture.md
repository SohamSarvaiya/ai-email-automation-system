# Architecture

```mermaid
flowchart LR
    A[Incoming Email<br/>POST /emails/process] --> B[Pydantic Validation]
    B --> C{method?}
    C -->|rules| D[RuleBasedClassifier]
    C -->|llm| E[LLMClassifier]
    C -->|both| D & E
    E -. API error .-> D
    D --> F[Final Category + Confidence]
    E --> F
    B --> G[Info Extractor<br/>order id, invoice, amount, phone, urgency]
    F --> H[Department Router]
    F --> I[Reply Drafter<br/>template or LLM]
    G --> I
    H --> J[(SQLite<br/>emails + activity_log)]
    I --> J
    F --> K{low confidence or<br/>rules != llm?}
    K -->|yes| L[needs_human_review = true]
    J --> M[GET /emails, /logs]
```

## Components

| Module | Responsibility |
|---|---|
| `app/schemas.py` | Pydantic models and the category -> department table |
| `app/classifiers/` | `BaseClassifier` (abstract) with `RuleBasedClassifier` and `LLMClassifier` |
| `app/extractor.py` | Regex based extraction of key fields |
| `app/drafter.py` | Reply drafts (templates; LLM when available) |
| `app/service.py` | `EmailProcessor` orchestrates the pipeline |
| `app/database.py` | SQLite persistence and activity log |
| `app/main.py` | FastAPI app factory and routes |

## Design decisions
- **Strategy pattern**: classifiers share one interface, so new ones (e.g. a fine-tuned model) plug in easily.
- **Dependency injection**: the LLM call is a plain function, so tests run offline with a fake.
- **Graceful degradation**: if the LLM fails, the pipeline falls back to rules and logs the error.
- **Human in the loop**: low confidence or rules/LLM disagreement sets `needs_human_review`.
