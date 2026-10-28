import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from . import database
from .ai_service import AIServiceError, extract_task
from .schemas import TaskCreate, TaskExtraction, TaskRecord, TaskStatusUpdate

# Load backend/.env when running locally from the project root or this folder.
load_dotenv(Path(__file__).resolve().parent / ".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield

app = FastAPI(
    title="AetherMind API",
    description="AI task extraction, validation, and SQLite storage for the CSB312 mini-project.",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    text: str = Field(min_length=5, max_length=3000)

class ExtractResponse(BaseModel):
    extracted: TaskExtraction

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AetherMind API is running", "docs": "/docs"}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/extract", response_model=ExtractResponse)
def extract(request: ExtractRequest) -> dict[str, Any]:
    text = request.text.strip()
    if len(text) < 5:
        raise HTTPException(status_code=422, detail="Please enter at least 5 characters.")
    try:
        result = extract_task(text)
        return {"extracted": result}
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.post("/tasks", response_model=TaskRecord, status_code=201)
def create_task(task: TaskCreate) -> dict[str, Any]:
    try:
        return database.create_task(task.model_dump())
    except Exception as exc:
        # Do not leak internal database details to the client.
        raise HTTPException(status_code=500, detail="Could not save the task to the database.") from exc

@app.get("/tasks", response_model=list[TaskRecord])
def get_tasks() -> list[dict[str, Any]]:
    try:
        return database.list_tasks()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not load tasks from the database.") from exc

@app.patch("/tasks/{task_id}/status", response_model=TaskRecord)
def set_task_status(task_id: int, update: TaskStatusUpdate) -> dict[str, Any]:
    if task_id < 1:
        raise HTTPException(status_code=422, detail="Task ID must be a positive integer.")
    result = database.update_status(task_id, update.status)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return result

@app.delete("/tasks/{task_id}", status_code=204)
def remove_task(task_id: int) -> None:
    if task_id < 1:
        raise HTTPException(status_code=422, detail="Task ID must be a positive integer.")
    if not database.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found.")
    return None
