"""
Attendance endpoints — fetches live data from PESU Academy.
Defaults to latest semester. Pass ?semester_id=... for a specific one.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

try:
    from .auth import get_current_user
    from .pesu_client import fetch_attendance
except ImportError:
    from auth import get_current_user
    from pesu_client import fetch_attendance

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("/summary")
async def attendance_summary(
    semester_id: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """Get overall attendance summary — fetched live from PESU Academy."""
    try:
        data = await fetch_attendance(user["username"], user["password"], semester_id)
        return {
            **data["summary"],
            "semesters": data.get("semesters", []),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch from PESU Academy: {str(e)}")


@router.get("/courses")
async def attendance_courses(
    semester_id: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """Get all courses with attendance — fetched live from PESU Academy."""
    try:
        data = await fetch_attendance(user["username"], user["password"], semester_id)
        return {
            "courses": data["courses"],
            "count": len(data["courses"]),
            "semesters": data.get("semesters", []),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch from PESU Academy: {str(e)}")


@router.get("/course/{course_code}")
async def attendance_course(
    course_code: str,
    semester_id: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """Get attendance for a single course — fetched live."""
    try:
        data = await fetch_attendance(user["username"], user["password"], semester_id)
        for course in data["courses"]:
            if course["course_code"] == course_code:
                return course
        raise HTTPException(status_code=404, detail=f"Course {course_code} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch from PESU Academy: {str(e)}")
