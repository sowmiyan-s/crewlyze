import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_update_status_endpoint():
    response = client.post("/api/system/update")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_query_sql_dataset_missing_session():
    # Calling query-sql with non-existent session should return 400
    response = client.post("/api/query-sql", data={"session_id": "nonexistent_session_123", "sql_query": "SELECT 1"})
    assert response.status_code == 400
    assert "Dataset not found" in response.json().get("detail", "")
