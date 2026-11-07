from datetime import date, datetime, timezone
from typing import Literal, Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from sqlmodel import Field as DBField
from sqlmodel import SQLModel

Priority = Literal["low", "medium", "high"]
Status = Literal["todo", "done"]
Language = Literal["ar", "en", "fr", "unknown"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(SQLModel, table=True):
    id: Optional[int] = DBField(default=None, primary_key=True)
    title: str = DBField(max_length=200)
    details: str = DBField(default="", max_length=5000)
    assignee: Optional[str] = DBField(default=None, max_length=120)
    priority: str = DBField(default="medium")
    due_date: Optional[date] = DBField(default=None)
    status: str = DBField(default="todo")
    language: str = DBField(default="unknown")
    created_at: datetime = DBField(default_factory=_utcnow)
    updated_at: datetime = DBField(default_factory=_utcnow)


class TaskCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=5000)
    assignee: Optional[str] = Field(default=None, max_length=120)
    priority: Priority = "medium"
    due_date: Optional[date] = None
    language: Language = "unknown"

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("assignee", mode="before")
    @classmethod
    def _normalize_assignee(cls, v: object) -> object:
        return (v.strip() or None) if isinstance(v, str) else v


class TaskUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    details: Optional[str] = Field(default=None, max_length=5000)
    assignee: Optional[str] = Field(default=None, max_length=120)
    priority: Optional[Priority] = None
    due_date: Optional[date] = None
    status: Optional[Status] = None
    language: Optional[Language] = None

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("assignee", mode="before")
    @classmethod
    def _normalize_assignee(cls, v: object) -> object:
        return (v.strip() or None) if isinstance(v, str) else v

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> "TaskUpdate":
        for f in ("title", "details", "priority", "status", "language"):
            if f in self.model_fields_set and getattr(self, f) is None:
                raise ValueError(f"{f} cannot be null")
        return self


class TaskRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    details: str
    assignee: Optional[str]
    priority: Priority
    due_date: Optional[date]
    status: Status
    language: Language
    created_at: datetime
    updated_at: datetime


class ExtractRequest(SQLModel):
    text: str = Field(min_length=10, max_length=8000)


class ExtractedTask(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=5000)
    assignee: Optional[str] = None
    priority: Optional[Priority] = None
    due_date: Optional[date] = None
    language: Language = "unknown"

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("assignee", mode="before")
    @classmethod
    def _normalize_assignee(cls, v: object) -> object:
        return (v.strip() or None) if isinstance(v, str) else v


class ExtractResponse(SQLModel):
    tasks: list[ExtractedTask]
