import pytest
from fastapi.testclient import TestClient
from main import app, is_safe_id, is_safe_filename, validate_project_id, get_safe_session_dir, get_safe_output_dir
from fastapi import HTTPException

client = TestClient(app)


def test_is_safe_id_valid():
    assert is_safe_id("project-123") is True
    assert is_safe_id("session_abc_456") is True
    assert is_safe_id("TestProject") is True


def test_is_safe_id_rejects_malicious_inputs():
    assert is_safe_id("") is False
    assert is_safe_id("../etc/passwd") is False
    assert is_safe_id("..\\windows\\system32") is False
    assert is_safe_id("project;rm -rf /") is False
    assert is_safe_id("test/123") is False
    assert is_safe_id("test\0null") is False
    assert is_safe_id("test with spaces") is False


def test_is_safe_filename():
    assert is_safe_filename("dataset.csv") is True
    assert is_safe_filename("sales_report_2024 (v1.2).csv") is True
    assert is_safe_filename("data [clean].csv") is True
    assert is_safe_filename("../dataset.csv") is False
    assert is_safe_filename("folder/dataset.csv") is False
    assert is_safe_filename("folder\\dataset.csv") is False
    assert is_safe_filename("") is False


def test_validate_project_id():
    assert validate_project_id("valid_id-99") == "valid_id-99"
    with pytest.raises(HTTPException) as excinfo:
        validate_project_id("../invalid")
    assert excinfo.value.status_code == 400


def test_get_safe_session_dir():
    path = get_safe_session_dir("test_session_id")
    assert "test_session_id" in str(path)


def test_api_projects_list():
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_system_info():
    response = client.get("/api/system/info")
    if response.status_code == 200:
        data = response.json()
        assert "version" in data or "status" in data


def test_orphan_session_recovery(tmp_path):
    import json
    import asyncio
    from main import lifespan
    from api.dependencies import SESSIONS_DIR

    test_session = SESSIONS_DIR / "orphan_test_session_recovery"
    test_session.mkdir(parents=True, exist_ok=True)
    meta_path = test_session / "metadata.json"
    done_path = test_session / "done.txt"

    if done_path.exists():
        done_path.unlink()

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"id": "orphan_test_session_recovery", "status": "running"}, f)

    async def run_lifespan():
        async with lifespan(app):
            pass

    asyncio.run(run_lifespan())

    with open(meta_path, "r", encoding="utf-8") as f:
        updated_meta = json.load(f)

    assert updated_meta["status"] == "interrupted"
    assert done_path.exists()

    # Clean up
    import shutil
    shutil.rmtree(test_session, ignore_errors=True)

