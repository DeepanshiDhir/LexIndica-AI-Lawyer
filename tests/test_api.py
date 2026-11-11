import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["LEGAL_AI_OFFLINE"] = "1"

from fastapi.testclient import TestClient
from app.api.server import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Indian Legal AI Assistant"
    assert data["indexes_present"] is True


def test_api_sources():
    response = client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert len(data["sources"]) > 0


def test_api_chat():
    payload = {
        "message": "Landlord deducted 20000 rupees from deposit for normal wall painting. Is this legal?",
        "session_id": "test_api_session"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["applicable_provisions"]) > 0
    assert data["safety_passed"] is True


def test_api_document_generation():
    payload = {
        "doc_type": "notice",
        "facts": {
            "tenant_name": "Kavita Reddy",
            "landlord_name": "Sunil Nair",
            "deposit_amount": "Rs. 40,000/-",
            "property_address": "Indiranagar, Bengaluru"
        }
    }
    response = client.post("/api/generate-document", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "document_text" in data
    assert "Kavita Reddy" in data["document_text"]
