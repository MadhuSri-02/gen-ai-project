import pytest
from pydantic import ValidationError
from backend.schemas import TaskCreate, TaskExtraction

def test_valid_task_schema():
    task = TaskCreate(title="Study FastAPI", due_date="2026-11-02", priority="High", notes="")
    assert task.title == "Study FastAPI"
    assert task.priority == "High"

def test_rejects_invalid_priority():
    with pytest.raises(ValidationError):
        TaskExtraction(title="Study FastAPI", priority="Urgent")

def test_rejects_short_title():
    with pytest.raises(ValidationError):
        TaskExtraction(title="ok")
