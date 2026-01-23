from app.core.security import hash_password

def get_user_by_email(conn, email: str):
    with conn.cursor() as cur:
        cur.execute(
            "select id, full_name, email, role, password_hash from users where email=%s limit 1",
            (email,),
        )
        return cur.fetchone()


def get_user_by_id(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "select id, full_name, email, role from users where id=%s limit 1",
            (user_id,),
        )
        return cur.fetchone()


def create_user(conn, full_name: str, email: str, role: str, password: str):
    pwd_hash = hash_password(password)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into users (full_name, email, role, password_hash)
            values (%s, %s, %s, %s)
            returning id, full_name, email, role
            """,
            (full_name, email, role, pwd_hash),
        )
        row = cur.fetchone()
    conn.commit()
    return row
