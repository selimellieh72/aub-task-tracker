from datetime import datetime, timezone

from fastapi import FastAPI, status

from app import storage
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus

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


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[TaskResponse]:
    return storage.get_all_tasks(status=status, priority=priority)
