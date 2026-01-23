from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.api.auth import get_current_user
from app.services.groups import create_group, list_my_groups

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreateIn(BaseModel):
    group_number: str = Field(min_length=3, max_length=30)  


def _require_teacher(user: dict):
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher can do this")


@router.post("")
def create(payload: GroupCreateIn, user=Depends(get_current_user), conn=Depends(get_conn)):
    _require_teacher(user)

    try:
        return create_group(conn, teacher_id=user["id"], group_number=payload.group_number)
    except ValueError:
        raise HTTPException(status_code=409, detail="Group already exists")


@router.get("/my")
def my_groups(user=Depends(get_current_user), conn=Depends(get_conn)):
    _require_teacher(user)
    return list_my_groups(conn, teacher_id=user["id"])
