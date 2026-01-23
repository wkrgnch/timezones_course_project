from pathlib import Path
from app.api.auth import router as auth_router
import psycopg
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.services.bootstrap import ensure_tables, ensure_timezones_loaded
from app.api.timezones import router as timezones_router
from app.api.groups import router as groups_router

app = FastAPI(title="Timezones Defense")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="ui")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(timezones_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")

CSV_PATH = BASE_DIR / "data" / "timezones.csv"
SQL_PATH = BASE_DIR / "app" / "sql" / "create_tables.sql"

@app.get("/")
def root():
    return RedirectResponse(url="/ui/")

@app.on_event("startup")
def startup():
    with psycopg.connect(settings.database_url) as conn:
        ensure_tables(conn, SQL_PATH)
        ensure_timezones_loaded(conn, CSV_PATH)
