import secrets
import string

import psycopg
from psycopg.errors import UniqueViolation

ALPHABET = string.ascii_uppercase + string.digits


def _generate_join_code(length: int = 8) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def create_group(conn, teacher_id: int, group_number: str) -> dict:
    group_number = group_number.strip()

    for _ in range(10):
        join_code = _generate_join_code(8)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into groups (teacher_id, group_number, join_code)
                    values (%s, %s, %s)
                    returning id, teacher_id, group_number, join_code, created_at
                    """,
                    (teacher_id, group_number, join_code),
                )
                row = cur.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "teacher_id": row[1],
                "group_number": row[2],
                "join_code": row[3],
                "created_at": row[4].isoformat(),
            }
        except UniqueViolation:
            conn.rollback()
            if group_exists(conn, teacher_id, group_number):
                raise ValueError("Group already exists")

    raise RuntimeError("Failed to generate unique join_code")


def group_exists(conn, teacher_id: int, group_number: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            select 1
            from groups
            where teacher_id=%s and group_number=%s
            limit 1
            """,
            (teacher_id, group_number),
        )
        return cur.fetchone() is not None


def list_my_groups(conn, teacher_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select id, teacher_id, group_number, join_code, created_at
            from groups
            where teacher_id=%s
            order by created_at desc
            """,
            (teacher_id,),
        )
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "teacher_id": r[1],
            "group_number": r[2],
            "join_code": r[3],
            "created_at": r[4].isoformat(),
        }
        for r in rows
    ]
