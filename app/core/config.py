import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@127.0.0.1:5432/timezones_course",
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

settings = Settings()
