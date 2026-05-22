"""
Results endpoints — fetches live data from PESU Academy.
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
        data = await fetch_results(user["username"], user["password"])
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch results: {str(e)}")
