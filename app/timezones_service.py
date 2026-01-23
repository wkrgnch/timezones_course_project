import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class TimezoneRow:
    region: str
    msk_offset_hours: int
    utc_offset_hours: int
    fias_code: str


def _norm(s: str) -> str:
    return (s or "").strip().lower().replace("ё", "е")

def _norm_region(s: str) -> str:
    s = (s or "").strip().lower().replace("ё", "е")
    # убираем г. / город
    s = re.sub(r"\bг\.\b|\bг\b|\bгород\b", " ", s)
    # убираем знаки пунктуации
    s = re.sub(r"[^a-zа-я0-9\s]+", " ", s)
    
    s = re.sub(r"\s+", " ", s).strip()
    return s




def _parse_int(value: str) -> int:
    if value is None:
        return 0

    v = str(value).strip()
    if not v:
        return 0

    low = v.lower().replace("ё", "е")

    
    if (("мск" in low) or ("msk" in low) or ("mck" in low)) and not re.search(r"\d", low):
        return 0
    if ("utc" in low) and not re.search(r"\d", low):
        return 0

    # Ищем первое целое число со знаком +3, -2, 4
    m = re.search(r"[-+]\s*\d+|\d+", low)
    if m:
        return int(m.group(0).replace(" ", ""))

    raise ValueError(f"Cannot parse offset from value: {value!r}")



def load_timezones(csv_path: Path) -> List[TimezoneRow]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    rows: List[TimezoneRow] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for r in reader:
            rows.append(
                TimezoneRow(
                    fias_code=str(r.get("Код КЛАДР (ФИАС)", "")).strip(),
                    region=str(r.get("Регион РФ", "")).strip(),
                    msk_offset_hours=_parse_int(str(r.get("Номер часовой зоны (по МСК)", "0"))),
                    utc_offset_hours=_parse_int(str(r.get("Номер часовой зоны (по UTC)", "0"))),
                )
            )
    return rows


def search_regions(rows: List[TimezoneRow], q: str, limit: int = 10) -> List[TimezoneRow]:
    nq = _norm(q)
    if not nq:
        return []
    out = [r for r in rows if nq in _norm(r.region)]
    return out[: max(1, min(limit, 50))]


def find_exact(rows: List[TimezoneRow], region: str) -> Optional[TimezoneRow]:
    nr = _norm_region(region)

    #точное совпадение после нормализации
    for r in rows:
        if _norm_region(r.region) == nr:
            return r

    #если не нашли - пробуем частичное совпадение
    for r in rows:
        if nr and nr in _norm_region(r.region):
            return r

    return None




def compute_times(row: TimezoneRow) -> dict:
    utc_now = datetime.now(timezone.utc)
    msk_now = datetime.now(ZoneInfo("Europe/Moscow"))

    local_now = utc_now + timedelta(hours=row.utc_offset_hours)

    return {
        "region": row.region,
        "msk_offset_hours": row.msk_offset_hours,
        "utc_offset_hours": row.utc_offset_hours,
        "msk_time": msk_now.strftime("%Y-%m-%d %H:%M"),
        "local_time": local_now.strftime("%Y-%m-%d %H:%M"),
    }
