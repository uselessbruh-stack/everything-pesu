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
async def get_results(semester: int = 1, user: dict = Depends(get_current_user)):
    """Get exam results for a semester — fetched live from PESU Academy."""
    try:
        data = await fetch_results(user["username"], user["password"], semester)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch results: {str(e)}")


@router.get("/semester/{semester}")
async def get_results_by_semester(semester: int, user: dict = Depends(get_current_user)):
    """Get results for a specific semester."""
    try:
        data = await fetch_results(user["username"], user["password"], semester)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch results: {str(e)}")
