from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
import pytest

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.email import Email

client = TestClient(app)


def test_webhook_sans_secret():
    r = client.post("/webhooks/n8n")
    assert r.status_code == 401


def test_webhook_mauvais_secret():
    r = client.post("/webhooks/n8n", headers={"X-Webhook-Secret": "mauvais"})
    assert r.status_code == 401


def test_webhook_bon_secret():
    old = settings.webhook_secret
    settings.webhook_secret = "test-secret"
    try:
        r = client.post(
            "/webhooks/n8n",
            headers={"X-Webhook-Secret": "test-secret"},
            json={"action": "ping"},
        )
        assert r.status_code == 200
    finally:
        settings.webhook_secret = old


def test_double_import_idempotent():
    db = SessionLocal()
    try:
        db.add(Email(gmail_message_id="test-dup-001", sender="a@b.c", subject="s", body="b"))
        db.commit()
        db.add(Email(gmail_message_id="test-dup-001", sender="x@y.z", subject="s2", body="b2"))
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.query(Email).filter(Email.gmail_message_id == "test-dup-001").delete()
        db.commit()
        db.close()


def test_double_envoi_idempotent():
    db = SessionLocal()
    try:
        e = Email(gmail_message_id="test-send-001", sender="a@b.c", subject="s", body="b")
        db.add(e)
        db.commit()
        eid = e.id
    finally:
        db.close()
    r1 = client.post(f"/emails/{eid}/send")
    r2 = client.post(f"/emails/{eid}/send")
    assert r1.status_code == 200 and r1.json()["sent"] is True
    assert r2.status_code == 200 and r2.json()["already_sent"] is True
    db = SessionLocal()
    try:
        db.query(Email).filter(Email.id == eid).delete()
        db.commit()
    finally:
        db.close()
