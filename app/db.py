import psycopg
from app.core.config import settings

def get_conn():
    with psycopg.connect(settings.database_url) as conn:
        yield conn
