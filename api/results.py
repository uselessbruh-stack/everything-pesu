"""
Results endpoints for PESU Academy API.
"""

from fastapi import APIRouter, Depends, HTTPException

try:
    from .auth import get_current_user
    from .data_loader import get_results, get_results_for_course
except ImportError:
    from auth import get_current_user
    from data_loader import get_results, get_results_for_course

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("")
async def all_results(user: dict = Depends(get_current_user)):
    """Get all exam results grouped by semester."""
    results = get_results()
    # Transform to a cleaner structure
    semesters = []
    for sem_name, sem_data in results.items():
        semesters.append({
            "semester": sem_name,
            "course_count": sem_data.get("course_count", 0),
            "type": sem_data.get("type", "unknown"),
            "courses": sem_data.get("courses", []),
        })

    # Sort semesters (Sem-2 first = most recent)
    semesters.sort(key=lambda s: s["semester"], reverse=True)
    return {"semesters": semesters}


@router.get("/course/{course_code}")
async def course_results(course_code: str, user: dict = Depends(get_current_user)):
    """Get results for a specific course across all semesters."""
    results = get_results_for_course(course_code)
    if not results:
        raise HTTPException(
            status_code=404, detail=f"No results found for course {course_code}"
        )
    return {"course_code": course_code, "results": results}
