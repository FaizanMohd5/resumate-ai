from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class Bullet(BaseModel):
    id: str
    text: str


class Entry(BaseModel):
    id: str
    title: str
    org: str | None = None
    dates: str | None = None
    bullets: list[Bullet] = Field(default_factory=list)


class Section(BaseModel):
    id: str
    name: str
    kind: Literal["text", "entries", "bullets"]
    content: str | None = None
    entries: list[Entry] | None = None
    bullets: list[Bullet] | None = None


class Resume(BaseModel):
    id: str
    owner: str
    title: str
    name: str | None = None
    contact: dict[str, str] = Field(default_factory=dict)
    sections: list[Section] = Field(default_factory=list)


class EditRequest(BaseModel):
    resume_id: str
    instruction: str = Field(min_length=1, max_length=4000)


class RevertRequest(BaseModel):
    resume_id: str


class ExportRequest(BaseModel):
    resume_id: str
