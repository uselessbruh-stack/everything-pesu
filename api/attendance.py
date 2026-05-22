"""
Attendance endpoints for PESU Academy API.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import get_current_user
from .data_loader import (
    calculate_attendance,
    clear_cache,
    get_course,
    get_courses,
    get_summary,
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


class CalculateRequest(BaseModel):
    course_code: Optional[str] = None
    current_attended: int
    current_total: int
    target_percentage: float = 85.0
    scenario: str = "attend"  # "attend" or "bunk"
    classes_count: int = 0


@router.get("/summary")
async def attendance_summary(user: dict = Depends(get_current_user)):
    """Get overall attendance summary. Cached for 5 minutes."""
    summary = get_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No attendance data found")
    return summary


@router.get("/courses")
async def attendance_courses(user: dict = Depends(get_current_user)):
    """Get all courses with attendance data. Cached for 30 minutes."""
    courses = get_courses()
    return {"courses": courses, "count": len(courses)}


@router.get("/course/{course_code}")
async def attendance_course(course_code: str, user: dict = Depends(get_current_user)):
    """Get detailed attendance for a single course."""
    course = get_course(course_code)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_code} not found")
    return course


@router.post("/sync")
async def sync_attendance(user: dict = Depends(get_current_user)):
    """Clear cache and reload data from file."""
    clear_cache()
    summary = get_summary()
    return {
        "message": "Data reloaded from source",
        "summary": summary,
    }


@router.post("/calculate")
async def calculate(body: CalculateRequest, user: dict = Depends(get_current_user)):
    """Calculate attendance scenarios (what-if analysis)."""
    if body.current_total < 0 or body.current_attended < 0:
        raise HTTPException(status_code=400, detail="Values cannot be negative")
    if body.current_attended > body.current_total:
        raise HTTPException(
            status_code=400, detail="Attended cannot exceed total classes"
        )
    if body.target_percentage <= 0 or body.target_percentage > 100:
        raise HTTPException(
            status_code=400, detail="Target percentage must be between 1 and 100"
        )
    if body.classes_count < 0 or body.classes_count > 500:
        raise HTTPException(
            status_code=400, detail="Classes count must be between 0 and 500"
        )

    result = calculate_attendance(
        current_attended=body.current_attended,
        current_total=body.current_total,
        target_percentage=body.target_percentage,
        scenario=body.scenario,
        classes_count=body.classes_count,
    )
    return result
