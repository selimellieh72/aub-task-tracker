"""Pydantic models for the Task Tracker (per ADR-001): task enums, the
create/update input models, and the API response model."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    """Strip surrounding whitespace and reject titles that are blank."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("title must not be blank")
    return stripped


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    assignee: Optional[str] = Field(default=None, max_length=100)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        return _validate_title(value)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    assignee: Optional[str] = Field(default=None, max_length=100)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_title(value)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str = ""
    assignee: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
