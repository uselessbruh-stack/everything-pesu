"""
PESU Academy live client — wraps the pesuacademy PyPI library.
Creates a fresh session per request (stateless for Vercel serverless).
"""

import logging
from pesuacademy import PESUAcademy

logger = logging.getLogger(__name__)


async def create_session(username: str, password: str) -> PESUAcademy:
    """Login to PESU Academy and return an authenticated session."""
    try:
        session = await PESUAcademy.login(username, password)
        return session
    except Exception as e:
        logger.error(f"PESU login failed for {username}: {e}")
        raise


async def fetch_attendance(username: str, password: str, semester: int = None) -> dict:
    """Fetch live attendance data from PESU Academy."""
    session = await create_session(username, password)
    try:
        raw = await session.get_attendance(semester)

        # raw is dict[int, list[Course]] — convert to our API format
        all_courses = []
        for sem_num, courses in raw.items():
            for course in courses:
                att = course.attendance
                attended = att.attended if att and att.attended is not None else 0
                total = att.total if att and att.total is not None else 0
                pct = att.percentage if att and att.percentage is not None else 0.0

                all_courses.append({
                    "course_code": course.code,
                    "course_name": course.title,
                    "semester": sem_num,
                    "attendance": {
                        "attended": attended,
                        "total": total,
                        "percentage": round(pct, 2),
                    },
                })

        # Build summary
        total_attended = sum(c["attendance"]["attended"] for c in all_courses)
        total_classes = sum(c["attendance"]["total"] for c in all_courses)
        overall_pct = (total_attended / total_classes * 100) if total_classes > 0 else 0

        summary = {
            "total_attended": total_attended,
            "total_classes": total_classes,
            "overall_percentage": round(overall_pct, 2),
            "courses_count": len(all_courses),
        }

        return {"summary": summary, "courses": all_courses}
    finally:
        await session.close()


async def fetch_profile(username: str, password: str) -> dict:
    """Fetch live profile data from PESU Academy."""
    session = await create_session(username, password)
    try:
        profile = await session.get_profile()
        personal = profile.personal

        return {
            "name": personal.name,
            "pesu_id": personal.pesu_id,
            "srn": personal.srn,
            "program": personal.program,
            "branch": personal.branch,
            "semester": personal.semester,
            "section": personal.section,
            "email": personal.email_id,
            "phone": personal.contact_no,
        }
    finally:
        await session.close()


async def fetch_courses(username: str, password: str, semester: int = None) -> dict:
    """Fetch registered courses from PESU Academy."""
    session = await create_session(username, password)
    try:
        raw = await session.get_courses(semester)

        semesters = {}
        for sem_num, courses in raw.items():
            semesters[str(sem_num)] = [
                {
                    "course_code": c.code,
                    "course_name": c.title,
                    "type": c.type,
                    "status": c.status,
                }
                for c in courses
            ]

        return {"semesters": semesters}
    finally:
        await session.close()


async def fetch_results(username: str, password: str, semester: int) -> dict:
    """Fetch exam results from PESU Academy."""
    session = await create_session(username, password)
    try:
        result = await session.get_results(semester)

        return {
            "semester": semester,
            "sgpa": getattr(result, "sgpa", None),
            "total_credits": getattr(result, "total_credits", None),
            "subjects": [
                {
                    "code": getattr(s, "code", ""),
                    "title": getattr(s, "title", ""),
                    "credits": getattr(s, "credits", 0),
                    "grade": getattr(s, "grade", ""),
                }
                for s in getattr(result, "subjects", [])
            ],
        }
    except ValueError as e:
        return {"semester": semester, "error": str(e), "subjects": []}
    finally:
        await session.close()
