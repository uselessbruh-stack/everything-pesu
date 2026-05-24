"""
Results endpoints — fetches live data from PESU Academy.
Defaults to latest semester. Pass ?semester_id=... for a specific one.
Returns { semesters: [{semester, type, sgpa, courses, course_count}] }
"""

from fastapi import APIRouter, Depends, HTTPException, Query

try:
    from .auth import get_current_user
    from .pesu_client import fetch_results
except ImportError:
    from auth import get_current_user
    from pesu_client import fetch_results

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("")
async def get_results(
    semester_id: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """Get exam results — scraped live from PESU Academy."""
    try:
        raw = await fetch_results(user["username"], user["password"], semester_id)

        # Transform: raw = {results: {"Sem-1": {...}, "Sem-2": {...}}, semesters: [...]}
        semesters = []
        for sem_name, sem_data in raw.get("results", {}).items():
            courses = sem_data.get("courses", [])
            # Ensure assessments/marks fields exist
            for course in courses:
                if "assessments" not in course:
                    course["assessments"] = {}
                if "marks" not in course:
                    # Build marks from assessments for the frontend
                    marks = {}
                    for assess_name, assess_data in course.get("assessments", {}).items():
                        score = assess_data.get("score", "")
                        max_val = assess_data.get("max", "")
                        if score and score != "NA" and max_val:
                            try:
                                marks[assess_name] = {
                                    "obtained": float(score),
                                    "total": float(max_val),
                                }
                            except ValueError:
                                pass
                    course["marks"] = marks

            semesters.append({
                "semester": sem_name,
                "type": sem_data.get("type", "unknown"),
                "sgpa": sem_data.get("sgpa"),
                "cgpa": sem_data.get("cgpa"),
                "courses": courses,
                "course_count": sem_data.get("course_count", len(courses)),
            })

        return {
            "semesters": semesters,
            "available_semesters": raw.get("semesters", []),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch results: {str(e)}")
