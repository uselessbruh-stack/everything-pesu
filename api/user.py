"""
User profile endpoint — fetches live data from PESU Academy.
Transforms profile data to match what the frontend expects.
"""

from fastapi import APIRouter, Depends, HTTPException

try:
    from .auth import get_current_user
    from .pesu_client import fetch_profile, fetch_attendance
except ImportError:
    from auth import get_current_user
    from pesu_client import fetch_profile, fetch_attendance

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get student profile — fetched live from PESU Academy."""
    try:
        profile = await fetch_profile(user["username"], user["password"])

        return {
            "username": profile.get("name", user["username"]),
            "pesu_id": profile.get("pesu_id", ""),
            "srn": profile.get("srn", ""),
            "program": profile.get("program", ""),
            "department": profile.get("branch", ""),
            "branch": profile.get("branch", ""),
            "semester": profile.get("semester", ""),
            "section": profile.get("section", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch profile: {str(e)}")
