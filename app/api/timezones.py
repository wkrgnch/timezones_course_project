from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import get_conn
from app.services.bootstrap import norm_region

router = APIRouter(prefix="/timezones", tags=["timezones"])


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _msk_now() -> datetime:
    # Москва = UTC+3 
    return datetime.now(timezone.utc) + timedelta(hours=3)


def _label(msk_offset_hours: int, utc_offset_hours: int) -> str:
    sign_msk = "+" if msk_offset_hours >= 0 else "-"
    sign_utc = "+" if utc_offset_hours >= 0 else "-"
    return f"МСК{sign_msk}{abs(msk_offset_hours)} (UTC{sign_utc}{abs(utc_offset_hours)})"


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    conn=Depends(get_conn),
):
    qq = q.strip()

    with conn.cursor() as cur:
        cur.execute(
            """
            select region, msk_offset_hours, utc_offset_hours, fias_code
            from timezones
            where region ilike %s
            order by region
            limit %s
            """,
            (f"%{qq}%", limit),
        )
        rows = cur.fetchall()

    return [
        {
            "region": r[0],
            "msk_offset_hours": int(r[1]),
            "utc_offset_hours": int(r[2]),
            "fias_code": r[3],
        }
        for r in rows
    ]


@router.get("/resolve")
def resolve(
    region: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    conn=Depends(get_conn),
):
    nr = norm_region(region)

    with conn.cursor() as cur:
        # точное совпадение по нормализованному названию
        cur.execute(
            """
            select region, msk_offset_hours, utc_offset_hours, fias_code
            from timezones
            where region_norm = %s
            order by msk_offset_hours desc, region
            limit %s
            """,
            (nr, limit),
        )
        rows = cur.fetchall()

        # если ничего не нашли - пробуем contains
        if not rows:
            cur.execute(
                """
                select region, msk_offset_hours, utc_offset_hours, fias_code
                from timezones
                where region_norm ilike %s
                order by msk_offset_hours desc, region
                limit %s
                """,
                (f"%{nr}%", limit),
            )
            rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Region not found")

    # чтобы не показывать одинаковые варианты несколько раз
    seen = set()
    variants = []
    for r in rows:
        key = (int(r[1]), int(r[2]))
        if key in seen:
            continue
        seen.add(key)

        msk = int(r[1])
        utc = int(r[2])

        variants.append(
            {
                "region": r[0],
                "msk_offset_hours": msk,
                "utc_offset_hours": utc,
                "fias_code": r[3],
                "label": _label(msk, utc),
            }
        )

    return {
        "input_region": region,
        "needs_choice": len(variants) > 1,
        "variants": variants,
    }


@router.get("/now")
def now(
    region: str | None = Query(default=None, min_length=1),
    fias_code: str | None = Query(default=None, min_length=1),
    conn=Depends(get_conn),
):
    row = None

    with conn.cursor() as cur:
        if fias_code:
            cur.execute(
                """
                select region, msk_offset_hours, utc_offset_hours, fias_code
                from timezones
                where fias_code = %s
                limit 1
                """,
                (fias_code,),
            )
            row = cur.fetchone()

        if row is None and region:
            nr = norm_region(region)

            cur.execute(
                """
                select region, msk_offset_hours, utc_offset_hours, fias_code
                from timezones
                where region_norm = %s
                order by msk_offset_hours desc, region
                limit 1
                """,
                (nr,),
            )
            row = cur.fetchone()

            if row is None:
                cur.execute(
                    """
                    select region, msk_offset_hours, utc_offset_hours, fias_code
                    from timezones
                    where region_norm ilike %s
                    order by msk_offset_hours desc, region
                    limit 1
                    """,
                    (f"%{nr}%",),
                )
                row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Region not found")

    db_region, msk_offset_hours, utc_offset_hours, db_fias = row
    msk_offset_hours = int(msk_offset_hours)
    utc_offset_hours = int(utc_offset_hours)

    msk_now = _msk_now()
    local_now = msk_now + timedelta(hours=msk_offset_hours)

    return {
        "region": db_region,
        "fias_code": db_fias,
        "msk_offset_hours": msk_offset_hours,
        "utc_offset_hours": utc_offset_hours,
        "label": _label(msk_offset_hours, utc_offset_hours),
        "msk_time": _fmt(msk_now),
        "local_time": _fmt(local_now),
    }
