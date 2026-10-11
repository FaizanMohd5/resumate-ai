from __future__ import annotations

from io import BytesIO
from uuid import uuid4
from docx import Document
from models import Resume, Section, Entry, Bullet

KNOWN_SECTIONS = {"summary", "profile", "experience", "work experience", "employment", "education", "skills", "projects", "certifications", "awards", "languages"}


def uid() -> str:
    return uuid4().hex[:12]


def _section_kind(name: str) -> str:
    low = name.lower()
    if low in {"summary", "profile", "objective"}:
        return "text"
    if low in {"experience", "work experience", "employment", "education", "projects"}:
        return "entries"
    return "bullets"


def parse_docx(content: bytes, filename: str, owner: str = "me") -> Resume:
    doc = Document(BytesIO(content))
    lines = [(p.text.strip(), p.style.name.lower()) for p in doc.paragraphs if p.text.strip()]
    title = filename.rsplit(".", 1)[0].replace("_", " ").title()
    name = lines[0][0] if lines else None
    contact = {}
    if len(lines) > 1 and ("@" in lines[1][0] or "|" in lines[1][0]):
        contact["details"] = lines[1][0]
    sections: list[Section] = []
    current: Section | None = None
    current_entry: Entry | None = None

    for i, (text, style) in enumerate(lines):
        if i < 2 and (text == name or text == contact.get("details")):
            continue
        is_heading = "heading" in style or text.lower().rstrip(":") in KNOWN_SECTIONS
        if is_heading:
            label = text.rstrip(":")
            current = Section(id=uid(), name=label, kind=_section_kind(label),
                              content="" if _section_kind(label) == "text" else None,
                              entries=[] if _section_kind(label) == "entries" else None,
                              bullets=[] if _section_kind(label) == "bullets" else None)
            sections.append(current); current_entry = None
            continue
        if not current:
            current = Section(id=uid(), name="Summary", kind="text", content="")
            sections.append(current)
        if current.kind == "text":
            current.content = " ".join(filter(None, [current.content, text]))
        elif current.kind == "bullets":
            current.bullets.append(Bullet(id=uid(), text=text.lstrip("•*- ").strip()))
        elif text.startswith(("•", "-", "*")) or "list" in style:
            if current_entry is None:
                current_entry = Entry(id=uid(), title="Details", bullets=[])
                current.entries.append(current_entry)
            current_entry.bullets.append(Bullet(id=uid(), text=text.lstrip("•*- ").strip()))
        else:
            parts = [x.strip() for x in text.split("|", 1)]
            current_entry = Entry(id=uid(), title=parts[0], org=parts[1] if len(parts) > 1 else None, bullets=[])
            current.entries.append(current_entry)
    if not sections:
        sections = [Section(id=uid(), name="Summary", kind="text", content="")]
    return Resume(id=uuid4().hex, owner=owner if owner in {"me", "friend"} else "me", title=title, name=name, contact=contact, sections=sections)
