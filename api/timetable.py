"""
Timetable endpoints — fetches live data from PESU Academy.
Transforms the raw schedule dict into structured objects the frontend expects.
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


def _schedule_to_classes(schedule: dict) -> list:
    """Convert {'8:00-9:00': 'UQ25CA651B-Algorithms...'} to structured list."""
    classes = []
    for time_slot, raw_info in sorted(schedule.items()):
        # raw_info is like "UQ25CA651B-Algorithms Analysis and Design"
        parts = raw_info.split("-", 1)
        course_code = parts[0].strip() if parts else raw_info
        course_name = parts[1].strip() if len(parts) > 1 else raw_info
        classes.append({
            "time": time_slot,
            "course_code": course_code,
            "course_name": course_name,
            "instructor": "",
        })
    return classes


@router.get("")
async def get_timetable(user: dict = Depends(get_current_user)):
    """Get today's timetable — scraped live from PESU Academy."""
    try:
        data = await fetch_timetable(user["username"], user["password"])
        today = datetime.now().strftime("%A")
        schedule = data.get("schedule", {})
        day_schedule = schedule.get(today, {})
        classes = _schedule_to_classes(day_schedule)

        return {
            "day": today,
            "classes": classes,
            "total_classes": len(classes),
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
        schedule = data.get("schedule", {})

        week = {}
        for day, day_schedule in schedule.items():
            week[day] = _schedule_to_classes(day_schedule)

        return {
            "week": week,
            "batch": data.get("batch", ""),
            "room": data.get("room", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch timetable: {str(e)}")
