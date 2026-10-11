from __future__ import annotations

import re
from copy import deepcopy
from uuid import uuid4
from models import Resume, Section, Entry, Bullet
from services.llm import LLMClient


def uid() -> str: return uuid4().hex[:12]


def _find_section(resume: Resume, phrase: str) -> Section | None:
    phrase = phrase.lower()
    return next((s for s in resume.sections if phrase in s.name.lower()), None)


def local_patch(resume: Resume, instruction: str) -> Resume:
    """Safe offline fallback: supports explicit add-bullet / add-section requests only."""
    result = deepcopy(resume); text = instruction.strip()
    bullet = re.search(r"add (?:a )?bullet under\s+(.+?)(?:\s+(?:about|saying|that says)\s+)['\"]?(.+?)['\"]?$", text, re.I)
    if bullet:
        target, value = bullet.group(1).strip(), bullet.group(2).strip().strip(".'\"")
        section_name, _, entry_name = target.partition(">")
        section = _find_section(result, section_name.strip())
        if section and value:
            if section.kind == "entries" and section.entries:
                needle = entry_name.strip().lower()
                entry = next((e for e in section.entries if needle and (needle in e.title.lower() or (e.org and needle in e.org.lower()))), section.entries[-1])
                entry.bullets.append(Bullet(id=uid(), text=value))
            elif section.kind == "bullets": section.bullets.append(Bullet(id=uid(), text=value))
        return result
    add_section = re.search(r"add (?:a )?(.+?) section(?: after (.+))?$", text, re.I)
    if add_section:
        name, after = add_section.group(1).strip().title(), add_section.group(2)
        if not _find_section(result, name):
            section = Section(id=uid(), name=name, kind="entries", entries=[])
            idx = next((i + 1 for i, s in enumerate(result.sections) if after and after.lower() in s.name.lower()), len(result.sections))
            result.sections.insert(idx, section)
    return result


def apply_instruction(resume: Resume, instruction: str, llm: LLMClient | None) -> Resume:
    if llm:
        try:
            updated = llm.edit(resume, instruction)
            if updated.id == resume.id: return updated
        except Exception:
            pass
    return local_patch(resume, instruction)
