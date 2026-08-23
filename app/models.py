"""Pydantic models for the Task Tracker (per ADR-001): task enums, the
create/update input models, and the API response model."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


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


def _normalize_tags(tags: list[str]) -> list[str]:
    """Trim + lowercase every tag, reject blank/overlong ones, dedupe (first wins)."""
    normalized: list[str] = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if not cleaned:
            raise ValueError("tags must not contain blank values")
        if len(cleaned) > 30:
            raise ValueError("each tag must be at most 30 characters")
        if "," in cleaned:
            raise ValueError("tags must not contain commas")  # the UI uses commas as the separator
        if cleaned not in normalized:
            normalized.append(cleaned)
    if len(normalized) > 10:
        raise ValueError("a task may have at most 10 tags")
    return normalized


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    assignee: Optional[str] = Field(default=None, max_length=100)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, value: list[str]) -> list[str]:
        return _normalize_tags(value)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    assignee: Optional[str] = Field(default=None, max_length=100)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_title(value)

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        return _normalize_tags(value)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str = ""
    assignee: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """True when an unfinished task's due date is before today (server local date)."""
        return (
            self.due_date is not None
            and self.due_date < date.today()
            and self.status != TaskStatus.DONE
        )
