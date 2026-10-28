from backend import database

def test_create_list_and_update_task(tmp_path):
    db = str(tmp_path / "test.db")
    task = {
        "title": "Finish project report",
        "due_date": "2026-11-02",
        "priority": "High",
        "notes": "Add screenshots",
    }
    created = database.create_task(task, db)
    assert created["id"] == 1
    assert created["status"] == "Pending"

    tasks = database.list_tasks(db)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Finish project report"

    updated = database.update_status(1, "Completed", db)
    assert updated["status"] == "Completed"

    assert database.delete_task(1, db) is True
    assert database.delete_task(1, db) is False
