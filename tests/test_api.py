import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

PAYLOAD = {"sender": "rahul@example.com", "subject": "My order is delayed",
           "body": "Order ORD-48213 not delivered yet. Urgent!"}


def make_client(tmp_path, llm=None):
    settings = Settings(database_path=str(tmp_path / "t.db"))
    return TestClient(create_app(settings, llm_complete=llm))


@pytest.fixture
def client(tmp_path):
    return make_client(tmp_path)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "llm_enabled": False}


def test_process_with_rules(client):
    r = client.post("/emails/process", json=PAYLOAD)
    assert r.status_code == 200
    d = r.json()
    assert d["final"]["category"] == "Order Support"
    assert d["department"] == "Support Team"
    assert d["priority"] == "high"
    assert d["extracted"]["order_ids"] == ["ORD-48213"]
    assert "Rahul" in d["draft_reply"] and "ORD-48213" in d["draft_reply"]


def test_saved_and_retrievable(client):
    email_id = client.post("/emails/process", json=PAYLOAD).json()["id"]
    assert client.get(f"/emails/{email_id}").json()["id"] == email_id
    assert len(client.get("/emails").json()) == 1
    assert client.get("/emails", params={"category": "Billing"}).json() == []


def test_404_for_unknown_email(client):
    assert client.get("/emails/999").status_code == 404


def test_validation_error(client):
    assert client.post("/emails/process", json={"sender": "a@b.com"}).status_code == 422


def test_llm_requested_without_key_returns_503(client):
    assert client.post("/emails/process?method=llm", json=PAYLOAD).status_code == 503


def test_activity_log_written(client):
    client.post("/emails/process", json=PAYLOAD)
    events = [e["event"] for e in client.get("/logs").json()]
    assert "email_received" in events and "email_processed" in events


def test_both_methods_flag_disagreement_for_review(tmp_path):
    fake = lambda s, u: '{"category": "Billing", "confidence": 0.95, "reasoning": "x"}'
    c = make_client(tmp_path, llm=fake)
    d = c.post("/emails/process?method=both", json=PAYLOAD).json()
    assert d["rule_result"]["category"] == "Order Support"
    assert d["llm_result"]["category"] == "Billing"
    assert d["agreement"] is False and d["needs_human_review"] is True


def test_llm_failure_falls_back_to_rules(tmp_path):
    def boom(s, u):
        raise RuntimeError("API down")
    d = make_client(tmp_path, llm=boom).post("/emails/process?method=llm", json=PAYLOAD).json()
    assert d["final"]["method"] == "rules"
