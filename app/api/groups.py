from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import get_conn
from app.api.auth import get_current_user
from app.services.groups import create_group, list_my_groups
from app.services.participants import get_group_by_code, upsert_participant, list_queue



router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreateIn(BaseModel):
    group_number: str = Field(min_length=3, max_length=30)  

class JoinIn(BaseModel):
    join_code: str = Field(min_length=4, max_length=20)
    region: str | None = Field(default=None, max_length=200)
    msk_offset_hours: int | None = Field(default=None, ge=-12, le=12)


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

@router.post("/join")
def join(payload: JoinIn, user=Depends(get_current_user), conn=Depends(get_conn)):
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only student can join")

    grp = get_group_by_code(conn, payload.join_code)
    if not grp:
        raise HTTPException(status_code=404, detail="Group not found")

    group_id = grp[0]

    # ФИО берём из профиля
    display_name = user.get("full_name") or user.get("email") or "Student"

    item = upsert_participant(
        conn,
        group_id=group_id,
        user_id=user["id"],
        display_name=display_name,
        region=payload.region,
        msk_offset_hours=payload.msk_offset_hours,
    )

    return {"group_id": group_id, "participant": item}


@router.get("/{group_id}/queue")
def queue(group_id: int, user=Depends(get_current_user), conn=Depends(get_conn)):
    _require_teacher(user)

    # проверим, что группа принадлежит этому преподавателю
    with conn.cursor() as cur:
        cur.execute(
            "select 1 from groups where id=%s and teacher_id=%s limit 1",
            (group_id, user["id"]),
        )
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Group not found")

    return {"group_id": group_id, "queue": list_queue(conn, group_id)}
