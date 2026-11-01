"""
Integration tests for FastAPI endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "postgresql"
    assert "version" in data


def test_invalid_persona_header():
    response = client.get("/api/workspace", headers={"x-demo-persona": "unknown_role"})
    assert response.status_code == 400
    assert "Unknown persona" in response.json()["detail"]


def test_openapi_schema_accessible():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AccessGuard"
    assert "/api/workspace" in schema["paths"]
    assert "/health" in schema["paths"]


def test_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text

