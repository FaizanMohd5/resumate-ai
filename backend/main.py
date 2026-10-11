from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from db import SessionLocal
from models import EditRequest, ExportRequest, RevertRequest
from repositories.resume_repo import SQLiteResumeRepository, initialize_database
from services.llm import GeminiLLMClient
from services.parser import parse_docx
from services.patcher import apply_instruction
from services.renderer import render_docx, render_html

repo = SQLiteResumeRepository()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database(); yield

app = FastAPI(title="Resumate", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/", include_in_schema=False)
def home(): return FileResponse(Path(__file__).parent / "static" / "index.html")

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/resumes")
def list_resumes(): return repo.list()

def payload(resume): return {"resume": resume.model_dump(), "preview_html": render_html(resume)}

@app.get("/resumes/{resume_id}")
def get_resume(resume_id: str):
    resume = repo.get(resume_id)
    if not resume: raise HTTPException(404, "Resume not found")
    return payload(resume)

@app.post("/upload")
async def upload(file: UploadFile = File(...), owner: str = Form("me")):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Upload a .docx file")
    content = await file.read()
    try: resume = parse_docx(content, file.filename, owner)
    except Exception as e: raise HTTPException(400, f"Could not parse Word file: {e}")
    repo.create(resume)
    return {"resume_id": resume.id, **payload(resume)}

@app.post("/edit")
def edit(request: EditRequest):
    resume = repo.get(request.resume_id)
    if not resume: raise HTTPException(404, "Resume not found")
    llm = GeminiLLMClient() if os.getenv("GEMINI_API_KEY") else None
    updated = apply_instruction(resume, request.instruction, llm)
    repo.save_edit(updated, request.instruction, resume)
    return payload(updated)

@app.post("/revert")
def revert(request: RevertRequest):
    resume = repo.revert_latest(request.resume_id)
    if not resume: raise HTTPException(404, "No edit to revert")
    return payload(resume)

@app.post("/export")
def export(request: ExportRequest):
    resume = repo.get(request.resume_id)
    if not resume: raise HTTPException(404, "Resume not found")
    filename = ''.join(c if c.isalnum() or c in '-_' else '_' for c in resume.title) + '.docx'
    return Response(render_docx(resume), media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={"Content-Disposition": f'attachment; filename="{filename}"'})
