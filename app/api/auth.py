from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from app.db import get_conn
from app.core.security import verify_password, create_access_token, decode_token
from app.services.users import get_user_by_email, create_user, get_user_by_id

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)



class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)
    role: str = Field(pattern="^(student|teacher)$")


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


@router.post("/register")
def register(payload: RegisterIn, conn=Depends(get_conn)):
    exists = get_user_by_email(conn, payload.email)
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")

    row = create_user(conn, payload.full_name, payload.email, payload.role, payload.password)
    token = create_access_token(user_id=row[0], role=row[3])
    return {
        "user": {"id": row[0], "full_name": row[1], "email": row[2], "role": row[3]},
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login")
def login(payload: LoginIn, conn=Depends(get_conn)):
    row = get_user_by_email(conn, payload.email)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, full_name, email, role, password_hash = row
    if not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user_id, role=role)
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    conn=Depends(get_conn),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing token")

    token = credentials.credentials

    try:
        data = decode_token(token)
        user_id = int(data.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"id": user[0], "full_name": user[1], "email": user[2], "role": user[3]}




@router.get("/me", dependencies=[Security(bearer_scheme)])
def me(user=Depends(get_current_user)):
    return {"user": user}


