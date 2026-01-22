import csv
import re
from pathlib import Path

def norm_region(s: str) -> str:
    s = (s or "").strip().lower().replace("ё", "е")
    s = re.sub(r"\bг\.\b|\bг\b|\bгород\b", " ", s)
    s = re.sub(r"[^a-zа-я0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_offset(value: str) -> int:
    v = (value or "").strip()
    if not v:
        return 0
    low = v.lower()

    if (("мск" in low) or ("msk" in low) or ("mck" in low)) and not re.search(r"\d", low):
        return 0
    if ("utc" in low) and not re.search(r"\d", low):
        return 0

    m = re.search(r"[-+]\s*\d+|\d+", low)
    if m:
        return int(m.group(0).replace(" ", ""))
    return 0

def ensure_tables(conn, sql_path: Path) -> None:
    sql = sql_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

def ensure_timezones_loaded(conn, csv_path: Path) -> int:
    with conn.cursor() as cur:
        cur.execute("select count(*) from timezones")
        count = cur.fetchone()[0]

    if count and count > 0:
        return 0

    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for r in reader:
            fias = (r.get("Код КЛАДР (ФИАС)") or "").strip()
            region = (r.get("Регион РФ") or "").strip()
            if not fias or not region:
                continue

            msk = parse_offset(str(r.get("Номер часовой зоны (по МСК)", "0")))
            utc = parse_offset(str(r.get("Номер часовой зоны (по UTC)", "0")))

            rows.append((fias, region, norm_region(region), msk, utc))

    with conn.cursor() as cur:
        cur.executemany(
            """
            insert into timezones (fias_code, region, region_norm, msk_offset_hours, utc_offset_hours)
            values (%s, %s, %s, %s, %s)
            on conflict (fias_code) do update set
                region = excluded.region,
                region_norm = excluded.region_norm,
                msk_offset_hours = excluded.msk_offset_hours,
                utc_offset_hours = excluded.utc_offset_hours
            """,
            rows,
        )
    conn.commit()
    return len(rows)
