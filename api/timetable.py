"""
Timetable endpoints for PESU Academy API.
"""

from datetime import datetime

from fastapi import APIRouter, Depends

try:
    from .auth import get_current_user
    from .data_loader import get_timetable, get_timetable_for_day
except ImportError:
    from auth import get_current_user
    from data_loader import get_timetable, get_timetable_for_day

router = APIRouter(prefix="/api/timetable", tags=["timetable"])

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse_slot(time_slot: str, raw_info: str) -> list[dict]:
    """Parse a timetable slot into structured class entries."""
    entries = []
    # Raw info can contain multiple classes separated by newlines
    parts = raw_info.split("\n")
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if not part:
            i += 1
            continue
        # Format: "COURSECODE-COURSE NAME"
        if "-" in part:
            code_name = part.split("-", 1)
            code = code_name[0].strip()
            name = code_name[1].strip() if len(code_name) > 1 else ""
            # Next line might be instructor
            instructor = ""
            if i + 1 < len(parts):
                next_part = parts[i + 1].strip().rstrip(",")
                # If next part doesn't look like a course code, it's an instructor
                if next_part and not any(c.isdigit() for c in next_part[:4]):
                    instructor = next_part
                    i += 1
            entries.append({
                "course_code": code,
                "course_name": name,
                "instructor": instructor,
                "time": time_slot,
            })
        i += 1
    return entries


@router.get("")
async def today_timetable(user: dict = Depends(get_current_user)):
    """Get today's schedule."""
    today = DAY_NAMES[datetime.now().weekday()]
    day_schedule = get_timetable_for_day(today)

    classes = []
    for time_slot, raw_info in day_schedule.items():
        classes.extend(_parse_slot(time_slot, raw_info))

    return {
        "day": today,
        "classes": classes,
        "total_classes": len(classes),
    }


@router.get("/week")
async def week_timetable(user: dict = Depends(get_current_user)):
    """Get full weekly schedule."""
    timetable = get_timetable()
    week = {}
    for day in DAY_NAMES[:6]:  # Mon-Sat
        day_schedule = timetable.get(day, {})
        classes = []
        for time_slot, raw_info in day_schedule.items():
            classes.extend(_parse_slot(time_slot, raw_info))
        if classes:
            week[day] = classes

    return {"week": week}
