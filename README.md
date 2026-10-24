# AI Email Automation System

A FastAPI service that reads incoming emails, classifies them, extracts key details, routes them to the right department, drafts a reply, and logs everything.

Built in two stages: **rule-based classification first**, then **LLM classification**, with a script to compare the two.

| Incoming email | Category | Routed to |
|---|---|---|
| My order is delayed | Order Support | Support Team |
| Need product pricing | Sales Inquiry | Sales Team |
| Cannot log in | Technical Support | IT Team |
| Please send invoice | Billing | Finance Team |
| anything unclear | General | Manual Review |

## Features
- Rule-based classifier (keyword scoring, subject weighted 2x) - works with no API key
- LLM classifier (Anthropic API) with automatic fallback to rules on failure
- `method=both` runs both and flags disagreements for human review
- Extraction of order IDs, invoice numbers, amounts, phones, emails, urgency
- Reply draft generation (templates, or LLM when configured)
- SQLite storage and a full activity log
- 28 automated tests, no network needed

## Architecture
See [docs/architecture.md](docs/architecture.md) for the diagram.

## Setup
```bash
git clone https://github.com/SohamSarvaiya/ai-email-automation-system.git
cd ai-email-automation-system
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add API_KEY to enable the LLM (optional)
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs for the interactive API documentation (Swagger UI).

## API
| Method | Endpoint | Description |
|---|---|---|
| POST | `/emails/process?method=rules\|llm\|both` | Run the full pipeline on one email |
| GET | `/emails?limit=50&category=Billing` | List processed emails |
| GET | `/emails/{id}` | Full result for one email |
| GET | `/logs` | Activity log |
| GET | `/health` | Health check and whether LLM is enabled |

Example:
```bash
curl -X POST "http://127.0.0.1:8000/emails/process?method=rules" \
  -H "Content-Type: application/json" \
  -d '{"sender":"rahul@example.com","subject":"My order is delayed","body":"Order ORD-48213 not delivered yet. Urgent!"}'
```
Response (trimmed):
```json
{
  "id": 1,
  "final": {"category": "Order Support", "confidence": 0.8, "method": "rules"},
  "department": "Support Team",
  "priority": "high",
  "needs_human_review": false,
  "extracted": {"order_ids": ["ORD-48213"], "urgent": true},
  "draft_reply": "Hi Rahul,\n\nThank you for contacting us about your order (ORD-48213)..."
}
```

## Rules vs LLM comparison
```bash
python -m scripts.compare_classifiers
```
Runs the 12 labelled emails in `samples/sample_emails.json` through both classifiers and prints accuracy.

Rules-only baseline: **9/12 (75%)**. The rules miss emails that don't use the expected keywords (e.g. "I want my money back", "Unable to access dashboard", "How much does the premium tier cost?"). Add your API key and run the script to record the LLM result here.

| Classifier | Accuracy on samples |
|---|---|
| Rules | 75% |
| LLM | _run the script and fill in_ |

## Tests
```bash
pytest -q
```

## Project structure
```
app/            FastAPI app, classifiers, extractor, drafter, DB
tests/          pytest suite
samples/        labelled sample emails
scripts/        classifier comparison script
docs/           architecture diagram
```

## Roadmap
- [ ] n8n workflow: Gmail trigger -> `POST /emails/process` -> Slack / email to department
- [ ] Gmail / IMAP inbox polling
- [ ] PostgreSQL option
- [ ] Docker image
- [ ] Attachment handling

