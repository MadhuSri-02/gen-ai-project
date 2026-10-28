from fastapi.testclient import TestClient
from backend.main import app
from backend import database

def test_health_and_validation(monkeypatch, tmp_path):
    test_db = str(tmp_path / "api.db")
    monkeypatch.setenv("DATABASE_PATH", test_db)
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"

        bad = client.post("/extract", json={"text": "no"})
        assert bad.status_code == 422

        created = client.post("/tasks", json={
            "title": "Study operating systems",
            "due_date": None,
            "priority": "Medium",
            "notes": ""
        })
        assert created.status_code == 201
        assert created.json()["title"] == "Study operating systems"

        listed = client.get("/tasks")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        missing = client.patch("/tasks/999/status", json={"status": "Completed"})
        assert missing.status_code == 404
