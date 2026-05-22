"""
Timetable endpoints.
The pesuacademy library doesn't support timetable scraping,
so we fall back to attendance_data.json if available, or return empty.
"""

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends

try:
    from .auth import get_current_user
except ImportError:
    from auth import get_current_user

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


def _load_timetable() -> dict:
    """Try to load timetable from the JSON file (static data)."""
    candidates = [
        Path(__file__).resolve().parent.parent / "attendance_data.json",
        Path(__file__).resolve().parent / "attendance_data.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("timetable", {})
            except Exception:
                pass
    return {}


@router.get("")
async def get_timetable(user: dict = Depends(get_current_user)):
    """Get today's timetable."""
    timetable = _load_timetable()
    today = datetime.now().strftime("%A")
    day_schedule = timetable.get(today, {})

    return {
        "day": today,
        "schedule": day_schedule,
        "note": "Timetable is loaded from cached data (live scraping not supported for timetable)"
    }


@router.get("/week")
async def get_weekly_timetable(user: dict = Depends(get_current_user)):
    """Get the full weekly timetable."""
    timetable = _load_timetable()
    return {
        "timetable": timetable,
        "note": "Timetable is loaded from cached data (live scraping not supported for timetable)"
    }
