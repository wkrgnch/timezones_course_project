from pathlib import Path
from typing import List

from fastapi import APIRouter, Query, HTTPException

from app.timezones_service import load_timezones, search_regions, find_exact, compute_times

router = APIRouter(prefix="/timezones", tags=["timezones"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV = BASE_DIR / "data" / "timezones.sample.csv"

# грузим один раз (без БД)
ROWS = load_timezones(DEFAULT_CSV)



@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)) -> List[dict]:
    found = search_regions(ROWS, q=q, limit=limit)
    return [
        {
            "region": r.region,
            "msk_offset_hours": r.msk_offset_hours,
            "utc_offset_hours": r.utc_offset_hours,
            "fias_code": r.fias_code,
        }
        for r in found
    ]


@router.get("/now")
def now(region: str = Query(..., min_length=1)) -> dict:
    row = find_exact(ROWS, region=region)
    if row is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return compute_times(row)
