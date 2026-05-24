"""
Results endpoints — fetches live data from PESU Academy.
Transforms data to match what the frontend expects:
  { semesters: [{ semester, type, courses, course_count }, ...] }
"""

from fastapi import APIRouter, Depends, HTTPException

try:
    from .auth import get_current_user
    from .pesu_client import fetch_results
except ImportError:
    from auth import get_current_user
    from pesu_client import fetch_results

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("")
async def get_results(user: dict = Depends(get_current_user)):
    """Get exam results — scraped live from PESU Academy."""
    try:
        raw = await fetch_results(user["username"], user["password"])

        # raw format: {"Sem-1": {sgpa, courses, course_count}, "Sem-2": {...}}
        # frontend expects: {semesters: [{semester, type, sgpa, courses, course_count}]}
        semesters = []
        for sem_name, sem_data in raw.items():
            courses = sem_data.get("courses", [])
            # Add empty assessments/marks if not present (frontend expects them)
            for course in courses:
                if "assessments" not in course:
                    course["assessments"] = {}
                if "marks" not in course:
                    course["marks"] = {}

            semesters.append({
                "semester": sem_name,
                "type": "completed" if sem_data.get("sgpa") else "ongoing",
                "sgpa": sem_data.get("sgpa"),
                "courses": courses,
                "course_count": sem_data.get("course_count", len(courses)),
            })

        return {"semesters": semesters}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch results: {str(e)}")
