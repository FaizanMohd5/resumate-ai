import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

db_path = os.environ.get("DB_PATH", str(Path(__file__).parent.parent / "data" / "resume.db"))
Path(db_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass
