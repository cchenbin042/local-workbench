from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, StringConstraints
from pydantic.alias_generators import to_camel


class PublicModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        allow_inf_nan=False,
    )


class FileSelection(PublicModel):
    file_id: UUID
    sheet: str | None = None


class TaskCreate(PublicModel):
    workspace_id: UUID
    sources: Annotated[list[FileSelection], Field(min_length=1)]
    prompt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    mode: Literal["agent", "profile"]


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


EventType = Literal[
    "task_started",
    "assistant_delta",
    "tool_started",
    "tool_finished",
    "source_ready",
    "artifact_ready",
    "cancel_requested",
    "task_cancelled",
    "task_failed",
    "task_completed",
]


class TaskEvent(PublicModel):
    task_id: UUID
    sequence: Annotated[int, Field(strict=True, ge=1)]
    type: EventType
    created_at: AwareDatetime
    payload: dict[str, JsonValue]
