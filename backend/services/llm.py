from __future__ import annotations

import os
from abc import ABC, abstractmethod
from google import genai
from google.genai import types
from models import Resume

SYSTEM_PROMPT = '''You edit a resume represented as JSON. Return only one valid Resume JSON object, with no prose or markdown. Make the minimal change required. Never invent facts, metrics, dates, employers, or qualifications. Preserve ids for every unchanged section, entry, and bullet. New nodes must use short uuid4 hex ids. If the request is ambiguous or impossible, return the resume unchanged.'''


class LLMClient(ABC):
    @abstractmethod
    def edit(self, resume: Resume, instruction: str) -> Resume: ...


class GeminiLLMClient(LLMClient):
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    def edit(self, resume: Resume, instruction: str) -> Resume:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"Resume JSON:\n{resume.model_dump_json()}\n\nInstruction: {instruction}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=Resume,
                temperature=0,
            ),
        )
        return Resume.model_validate_json(response.text or resume.model_dump_json())
