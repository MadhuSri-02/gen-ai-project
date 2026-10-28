from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

Priority = Literal["Low", "Medium", "High"]
Status = Literal["Pending", "Completed"]

class TaskExtraction(BaseModel):
    """Expected fields returned by the AI. Unknown dates must remain null."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    due_date: Optional[date] = None
    priority: Priority = "Medium"
    notes: str = Field(default="", max_length=1000)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Task title cannot be blank")
        return value

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str) -> str:
        return value.strip()

class TaskCreate(TaskExtraction):
    pass

class TaskRecord(TaskExtraction):
    id: int
    status: Status
    created_at: str

class TaskStatusUpdate(BaseModel):
    status: Status
