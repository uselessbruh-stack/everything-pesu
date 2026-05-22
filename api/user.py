"""
User profile endpoints for PESU Academy API.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .auth import get_current_user
from .data_loader import get_user_profile

router = APIRouter(prefix="/api/user", tags=["user"])


class SettingsUpdate(BaseModel):
    target_percentage: float = 85.0
    notifications_enabled: bool = False


# In-memory settings store (per-user in a real app)
_user_settings: dict = {
    "target_percentage": 85.0,
    "notifications_enabled": False,
}


@router.get("/profile")
async def profile(user: dict = Depends(get_current_user)):
    """Get user profile information."""
    profile_data = get_user_profile()
    return profile_data


@router.put("/settings")
async def update_settings(body: SettingsUpdate, user: dict = Depends(get_current_user)):
    """Update user settings."""
    _user_settings["target_percentage"] = body.target_percentage
    _user_settings["notifications_enabled"] = body.notifications_enabled
    return {"message": "Settings updated", "settings": _user_settings}


@router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    """Get user settings."""
    return _user_settings
