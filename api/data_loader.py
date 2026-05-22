"""
Data loader and caching layer for PESU Academy data.
Reads from attendance_data.json and provides cached access.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

# In-memory cache
_cache: dict[str, dict[str, Any]] = {}
_raw_data: Optional[dict] = None

# Cache TTLs in seconds
CACHE_TTL = {
    "summary": 300,       # 5 minutes
    "courses": 1800,      # 30 minutes
    "timetable": 3600,    # 1 hour
    "results": 3600,      # 1 hour
    "profile": 3600,      # 1 hour ddfdf dfdf df d
}

def _find_data_file() -> Path:
    """Locate attendance_data.json — check multiple paths for Vercel compatibility."""
    candidates = [
        Path(__file__).resolve().parent.parent / "attendance_data.json",  # root (local dev)
        Path(__file__).resolve().parent / "attendance_data.json",         # api/ folder
        Path("/var/task") / "attendance_data.json",                       # Vercel serverless
        Path("/var/task") / "api" / "attendance_data.json",               # Vercel alt
    ]
    for p in candidates:
        if p.exists():
            return p
    # Fallback to root path even if it doesn't exist yet
    return candidates[0]


DATA_FILE = _find_data_file()


def _load_raw_data() -> dict:
    """Load raw JSON data from file."""
    global _raw_data
    if _raw_data is None:
        if not DATA_FILE.exists():
            raise FileNotFoundError(
                f"attendance_data.json not found. Searched: {DATA_FILE}. "
                "Run the scraper first or ensure the file is deployed."
            )
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            _raw_data = json.load(f)
    return _raw_data


def _get_cached(key: str) -> Optional[Any]:
    """Get a value from cache if not expired."""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["time"] < CACHE_TTL.get(key, 300):
            return entry["data"]
    return None


def _set_cached(key: str, data: Any) -> None:
    """Store a value in cache."""
    _cache[key] = {"data": data, "time": time.time()}


def clear_cache() -> None:
    """Clear all cached data and force reload from file."""
    global _cache, _raw_data
    _cache = {}
    _raw_data = None


def get_summary() -> dict:
    """Get attendance summary."""
    cached = _get_cached("summary")
    if cached is not None:
        return cached

    data = _load_raw_data()
    summary = data.get("summary", {})
    _set_cached("summary", summary)
    return summary


def get_courses() -> list[dict]:
    """Get all courses with attendance data."""
    cached = _get_cached("courses")
    if cached is not None:
        return cached

    data = _load_raw_data()
    courses = data.get("courses", [])
    _set_cached("courses", courses)
    return courses


def get_course(course_code: str) -> Optional[dict]:
    """Get a single course by code."""
    courses = get_courses()
    for course in courses:
        if course.get("course_code") == course_code:
            return course
    return None


def get_timetable() -> dict:
    """Get the full timetable."""
    cached = _get_cached("timetable")
    if cached is not None:
        return cached

    data = _load_raw_data()
    timetable = data.get("timetable", {})
    _set_cached("timetable", timetable)
    return timetable


def get_timetable_for_day(day: str) -> dict:
    """Get timetable for a specific day."""
    timetable = get_timetable()
    return timetable.get(day, {})


def get_results() -> dict:
    """Get all results data."""
    cached = _get_cached("results")
    if cached is not None:
        return cached

    data = _load_raw_data()
    results = data.get("results", {})
    _set_cached("results", results)
    return results


def get_results_for_course(course_code: str) -> list[dict]:
    """Get results for a specific course across all semesters."""
    results = get_results()
    course_results = []
    for semester, sem_data in results.items():
        for course in sem_data.get("courses", []):
            if course.get("course_code") == course_code:
                course_results.append({
                    "semester": semester,
                    **course,
                })
    return course_results


def get_calendar() -> dict:
    """Get calendar events."""
    data = _load_raw_data()
    return data.get("calendar", {"events": [], "event_count": 0})


def get_user_profile() -> dict:
    """Get user profile info (without sensitive credentials)."""
    data = _load_raw_data()
    user = data.get("user", {})
    summary = data.get("summary", {})
    return {
        "username": user.get("username", ""),
        "last_synced": user.get("timestamp", ""),
        "department": "MCA",
        "program": "Master of Computer Applications",
        "semester": "Sem-2",
        "courses_count": summary.get("courses_count", 0),
    }


def calculate_attendance(
    current_attended: int,
    current_total: int,
    target_percentage: float,
    scenario: str = "attend",
    classes_count: int = 0,
) -> dict:
    """Calculate attendance scenarios."""
    if current_total == 0:
        return {
            "error": "Total classes cannot be zero",
            "new_attended": 0,
            "new_total": 0,
            "new_percentage": 0,
            "meets_target": False,
            "classes_needed_to_target": 0,
            "classes_can_bunk": 0,
        }

    # Scenario calculation
    if scenario == "attend":
        new_attended = current_attended + classes_count
        new_total = current_total + classes_count
    elif scenario == "bunk":
        new_attended = current_attended
        new_total = current_total + classes_count
    else:
        new_attended = current_attended
        new_total = current_total

    new_percentage = (new_attended / new_total * 100) if new_total > 0 else 0

    # Classes needed to reach target
    if target_percentage >= 100:
        classes_needed = max(0, new_total - new_attended)
    else:
        raw = (target_percentage * new_total - new_attended * 100) / (100 - target_percentage)
        classes_needed = max(0, int(raw) + (1 if raw > int(raw) else 0))

    # Classes can safely bunk
    if new_percentage >= target_percentage:
        raw_bunk = (new_attended * 100 / target_percentage) - new_total
        classes_can_bunk = max(0, int(raw_bunk))
    else:
        classes_can_bunk = 0

    return {
        "scenario_type": scenario,
        "classes_to_process": classes_count,
        "new_attended": new_attended,
        "new_total": new_total,
        "new_percentage": round(new_percentage, 2),
        "meets_target": new_percentage >= target_percentage,
        "classes_needed_to_target": classes_needed,
        "classes_can_bunk": classes_can_bunk,
    }
