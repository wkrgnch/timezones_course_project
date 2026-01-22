from pathlib import Path

import psycopg
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.services.bootstrap import ensure_tables, ensure_timezones_loaded
from app.api.timezones import router as timezones_router

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
CSV_PATH = BASE_DIR / "data" / "timezones.csv"
SQL_PATH = BASE_DIR / "app" / "sql" / "create_tables.sql"

app = FastAPI(title="Timezones Course Project")

# API
app.include_router(timezones_router, prefix="/api/v1")

# Фронт 
if FRONTEND_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/ui/")

@app.on_event("startup")
def startup():
    with psycopg.connect(settings.database_url) as conn:
        ensure_tables(conn, SQL_PATH)
        ensure_timezones_loaded(conn, CSV_PATH)
