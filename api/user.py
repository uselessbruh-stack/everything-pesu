"""
User profile endpoints — fetches live data from PESU Academy.
"""

from fastapi import APIRouter, Depends, HTTPException

try:
    from .auth import get_current_user
    from .pesu_client import fetch_profile
except ImportError:
    from auth import get_current_user
    from pesu_client import fetch_profile

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get student profile — fetched live from PESU Academy."""
    try:
        data = await fetch_profile(user["username"], user["password"])
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch profile: {str(e)}")
