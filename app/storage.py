"""In-memory storage layer for the Task Tracker (per ADR-001).

Tasks live in a module-level dict keyed by id. The JSON file persistence
(tasks.json) called for by ADR-001 comes in a later step and should hook into
this module without changing any of the function signatures below.
"""

from datetime import datetime, timezone
from typing import Optional

from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

_tasks: dict[int, TaskResponse] = {}
_next_id: int = 1


def _now() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(timezone.utc)


def add_task(task: TaskCreate) -> TaskResponse:
    """Store a new task and return it with its assigned id and timestamps."""
    global _next_id

    task_id = _next_id
    _next_id += 1

    timestamp = _now()
    created = TaskResponse(
        id=task_id,
        **task.model_dump(),
        created_at=timestamp,
        updated_at=timestamp,
    )
    _tasks[task_id] = created
    return created


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    overdue: Optional[bool] = None,
    tag: Optional[str] = None,
) -> list[TaskResponse]:
    """Return tasks in insertion (id) order, optionally filtered by status/priority/overdue/tag."""
    wanted_tag = tag.strip().lower() if tag is not None else None
    return [
        task
        for task in _tasks.values()
        if (status is None or task.status == status)
        and (priority is None or task.priority == priority)
        and (overdue is None or task.is_overdue == overdue)
        and (wanted_tag is None or wanted_tag in task.tags)
    ]


def get_task_by_id(task_id: int) -> Optional[TaskResponse]:
    """Return the task with this id, or None if it does not exist."""
    return _tasks.get(task_id)


def update_task(task_id: int, updates: TaskUpdate) -> Optional[TaskResponse]:
    """Apply the fields that were explicitly set, or None if the task is missing."""
    existing = _tasks.get(task_id)
    if existing is None:
        return None

    changes = updates.model_dump(exclude_unset=True)
    if changes.get("description", "") is None:
        changes["description"] = ""  # response model requires a str
    if changes.get("tags", []) is None:
        changes["tags"] = []  # response model requires a list; null means "clear"
    updated = existing.model_copy(update={**changes, "updated_at": _now()})
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: int) -> bool:
    """Remove a task; True if it existed, False otherwise."""
    return _tasks.pop(task_id, None) is not None


def _reset() -> None:
    """Clear all tasks and restart id numbering (test helper)."""
    global _next_id

    _tasks.clear()
    _next_id = 1
