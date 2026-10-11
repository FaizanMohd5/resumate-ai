"""Creates the smoke-test document. Run with backend dependencies installed."""
from pathlib import Path
import sys
sys.path.insert(0, "/app" if Path("/app").exists() else str(Path(__file__).parents[1] / "backend"))
from models import Resume, Section, Entry, Bullet
from services.renderer import render_docx

resume = Resume(id="sample", owner="friend", title="Arjun Patel Civil Engineer", name="Arjun Patel",
    contact={"details": "Pune, India | arjun.patel@example.com | +91 98765 43210"}, sections=[
    Section(id="summary", name="Summary", kind="text", content="Civil engineer with five years of experience supporting residential construction, site coordination, and quality control."),
    Section(id="experience", name="Experience", kind="entries", entries=[
        Entry(id="siteeng", title="Site Engineer", org="Buildwell Projects", dates="2022 - Present", bullets=[
            Bullet(id="b1", text="Coordinated daily site activities for mid-rise residential construction."),
            Bullet(id="b2", text="Prepared progress reports and supported quality inspections.")]),
        Entry(id="junior", title="Junior Civil Engineer", org="UrbanWorks", dates="2020 - 2022", bullets=[Bullet(id="b3", text="Assisted with quantity checks and contractor coordination.")])]),
    Section(id="education", name="Education", kind="entries", entries=[Entry(id="degree", title="B.E. Civil Engineering", org="Pune University", dates="2020", bullets=[])]),
    Section(id="skills", name="Skills", kind="bullets", bullets=[Bullet(id="s1", text="AutoCAD"), Bullet(id="s2", text="Site supervision"), Bullet(id="s3", text="Quantity estimation")])])
Path(__file__).with_name("sample_resume.docx").write_bytes(render_docx(resume))
