import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

_PBKDF2_ITERATIONS = 210_000  


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, dklen=32)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8").rstrip("=")
    dk_b64 = base64.urlsafe_b64encode(dk).decode("utf-8").rstrip("=")
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt_b64}${dk_b64}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_b64, dk_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters)

        pad = lambda s: s + "=" * (-len(s) % 4)
        salt = base64.urlsafe_b64decode(pad(salt_b64).encode("utf-8"))
        dk_expected = base64.urlsafe_b64decode(pad(dk_b64).encode("utf-8"))

        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
        return hmac.compare_digest(dk, dk_expected)
    except Exception:
        return False


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
