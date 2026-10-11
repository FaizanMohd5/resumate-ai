from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import ForeignKey, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column
from db import Base, engine, SessionLocal
from models import Resume


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResumeRow(Base):
    __tablename__ = "resumes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class EditRow(Base):
    __tablename__ = "edits"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    before: Mapped[str] = mapped_column(Text, nullable=False)
    after: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ResumeRepository(ABC):
    @abstractmethod
    def create(self, resume: Resume) -> None: ...
    @abstractmethod
    def get(self, resume_id: str) -> Resume | None: ...
    @abstractmethod
    def list(self) -> list[dict]: ...
    @abstractmethod
    def save_edit(self, resume: Resume, instruction: str, before: Resume) -> None: ...
    @abstractmethod
    def revert_latest(self, resume_id: str) -> Resume | None: ...


class SQLiteResumeRepository(ResumeRepository):
    def create(self, resume: Resume) -> None:
        with SessionLocal.begin() as s:
            s.add(ResumeRow(id=resume.id, owner=resume.owner, title=resume.title,
                data=resume.model_dump_json(), created_at=now(), updated_at=now()))

    def get(self, resume_id: str) -> Resume | None:
        with SessionLocal() as s:
            row = s.get(ResumeRow, resume_id)
            return Resume.model_validate_json(row.data) if row else None

    def list(self) -> list[dict]:
        with SessionLocal() as s:
            rows = s.scalars(select(ResumeRow).order_by(ResumeRow.updated_at.desc())).all()
            return [{"id": r.id, "title": r.title, "updated_at": r.updated_at} for r in rows]

    def save_edit(self, resume: Resume, instruction: str, before: Resume) -> None:
        with SessionLocal.begin() as s:
            row = s.get(ResumeRow, resume.id)
            if not row:
                raise KeyError(resume.id)
            row.data, row.title, row.updated_at = resume.model_dump_json(), resume.title, now()
            s.add(EditRow(id=uuid4().hex, resume_id=resume.id, instruction=instruction,
                before=before.model_dump_json(), after=resume.model_dump_json(), created_at=now()))

    def revert_latest(self, resume_id: str) -> Resume | None:
        with SessionLocal.begin() as s:
            edit = s.scalars(select(EditRow).where(EditRow.resume_id == resume_id)
                .order_by(EditRow.created_at.desc())).first()
            row = s.get(ResumeRow, resume_id)
            if not edit or not row:
                return None
            row.data, row.updated_at = edit.before, now()
            return Resume.model_validate_json(edit.before)


def initialize_database() -> None:
    Base.metadata.create_all(engine)
