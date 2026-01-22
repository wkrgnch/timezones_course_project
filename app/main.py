from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.timezones import router as timezones_router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

app = FastAPI(title="Online Defense Priority", version="0.2.0")

# статика фронта
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# API (без БД)
app.include_router(timezones_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/student", include_in_schema=False)
def student_page():
    return FileResponse(FRONTEND_DIR / "student.html")

@app.get("/teacher", include_in_schema=False)
def teacher_page():
    return FileResponse(FRONTEND_DIR / "teacher.html")
