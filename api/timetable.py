"""
Timetable endpoints — fetches live data from PESU Academy.
Parses inline JSON from timetable page for structured schedule data.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

try:
    from .auth import get_current_user
    from .pesu_client import fetch_timetable
except ImportError:
    from auth import get_current_user
    from pesu_client import fetch_timetable

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


@router.get("")
async def get_timetable(user: dict = Depends(get_current_user)):
    """Get today's timetable — scraped live from PESU Academy."""
    try:
        data = await fetch_timetable(user["username"], user["password"])
        today = datetime.now().strftime("%A")
        schedule = data.get("schedule", {})
        day_classes = schedule.get(today, [])

        return {
            "day": today,
            "classes": day_classes,
            "total_classes": len(day_classes),
            "batch": data.get("batch", ""),
            "room": data.get("room", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch timetable: {str(e)}")


@router.get("/week")
async def get_weekly_timetable(user: dict = Depends(get_current_user)):
    """Get the full weekly timetable — scraped live."""
    try:
        data = await fetch_timetable(user["username"], user["password"])
        return {
            "week": data.get("schedule", {}),
            "batch": data.get("batch", ""),
            "room": data.get("room", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch timetable: {str(e)}")
