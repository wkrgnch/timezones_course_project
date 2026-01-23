from datetime import datetime, timezone


def get_group_by_code(conn, join_code: str):
    with conn.cursor() as cur:
        cur.execute(
            "select id, teacher_id, group_number, join_code from groups where join_code=%s limit 1",
            (join_code.strip().upper(),),
        )
        return cur.fetchone()


def local_hour_from_msk_offset(msk_offset_hours: int) -> int:
    # local_time = now_msk + offset
    now_utc = datetime.now(timezone.utc)
    now_msk_hour = (now_utc.hour + 3) % 24  # МСК = UTC+3
    return (now_msk_hour + int(msk_offset_hours)) % 24


def calc_position(msk_offset_hours: int | None) -> int:
    # Чем позже местный час - тем выше приоритет
    # Для общей очереди position=0.
    if msk_offset_hours is None:
        return 0
    return local_hour_from_msk_offset(msk_offset_hours)


def upsert_participant(
    conn,
    group_id: int,
    user_id: int,
    display_name: str,
    region: str | None,
    msk_offset_hours: int | None,
) -> dict:
    position = calc_position(msk_offset_hours)

    with conn.cursor() as cur:
        cur.execute(
            """
            insert into participants (group_id, user_id, display_name, region, msk_offset_hours, position)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (group_id, user_id) do update
                set display_name=excluded.display_name,
                    region=excluded.region,
                    msk_offset_hours=excluded.msk_offset_hours,
                    position=excluded.position,
                    joined_at=now()
            returning id, group_id, user_id, display_name, region, msk_offset_hours, joined_at, position
            """,
            (group_id, user_id, display_name, region, msk_offset_hours, position),
        )
        row = cur.fetchone()

    conn.commit()
    return {
        "id": row[0],
        "group_id": row[1],
        "user_id": row[2],
        "display_name": row[3],
        "region": row[4],
        "msk_offset_hours": row[5],
        "joined_at": row[6].isoformat(),
        "position": row[7],
    }


def list_queue(conn, group_id: int) -> list[dict]:
    # Сначала те, у кого position > 0 (с учетом, что есть регион), по убыванию position,
    # потом общая очередь (где position=0) по joined_at
    with conn.cursor() as cur:
        cur.execute(
            """
            select id, group_id, user_id, display_name, region, msk_offset_hours, joined_at, position
            from participants
            where group_id=%s
            order by
                case when position > 0 then 0 else 1 end,
                position desc,
                joined_at asc
            """,
            (group_id,),
        )
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "group_id": r[1],
            "user_id": r[2],
            "display_name": r[3],
            "region": r[4],
            "msk_offset_hours": r[5],
            "joined_at": r[6].isoformat(),
            "position": r[7],
        }
        for r in rows
    ]
