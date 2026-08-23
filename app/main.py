from datetime import datetime, timezone

from fastapi import FastAPI, status

from app import storage
from app.models import TaskCreate, TaskResponse

app = FastAPI(
    title="Task Tracker API",
    description="Module 1 Task Tracker learning project (no auth, no database — in-memory + JSON file persistence per ADR-001)",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
)
def create_task(payload: TaskCreate) -> TaskResponse:
    return storage.add_task(payload)
