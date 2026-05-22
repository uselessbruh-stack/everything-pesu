from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from api.auth import verify_jwt_token
from api.config import settings, cache

router = APIRouter(prefix="/api/user", tags=["user"])

# --- Request Models ---
class SettingsUpdate(BaseModel):
    target_percentage: float = 85.0
    theme: Optional[str] = "dark"
    enable_notifications: Optional[bool] = True

# --- Routes ---

@router.get("/profile")
async def get_profile(current_user: dict = Depends(verify_jwt_token)):
    """Retrieve details of the logged-in student"""
    username = current_user["username"]
    
    # Capitalize username for displaying as SRN
    srn = username.upper()
    
    return {
        "success": True,
        "data": {
            "name": "Alex Mercer",
            "srn": srn,
            "email": f"{username.lower()}@stu.pes.edu",
            "department": "Master of Computer Applications",
            "program": "M.C.A. (Post Graduate)",
            "semester": "Semester 2",
            "section": "Sec-B",
            "avatar_url": f"https://api.dicebear.com/7.x/initials/svg?seed={username}&backgroundColor=4f46e5"
        }
    }

@router.get("/settings")
async def get_settings(current_user: dict = Depends(verify_jwt_token)):
    """Get student preferences and global settings"""
    username = current_user["username"]
    cache_key = f"settings:{username}"
    
    user_settings = cache.get(cache_key)
    if not user_settings:
        # Default settings
        user_settings = {
            "target_percentage": 85.0,
            "theme": "dark",
            "enable_notifications": True
        }
        cache.set(cache_key, user_settings, 86400 * 30) # Cache for 30 days
        
    return {"success": True, "data": user_settings}

@router.put("/settings")
async def update_settings(update_data: SettingsUpdate, current_user: dict = Depends(verify_jwt_token)):
    """Update student preferences (like global target percentage)"""
    username = current_user["username"]
    cache_key = f"settings:{username}"
    
    user_settings = {
        "target_percentage": update_data.target_percentage,
        "theme": update_data.theme,
        "enable_notifications": update_data.enable_notifications
    }
    
    cache.set(cache_key, user_settings, 86400 * 30)
    
    # Also invalidate course summaries if the target percentage changes,
    # so they reload with correct progress stats relative to new target
    cache.delete(f"courses:{username}")
    cache.delete(f"summary:{username}")
    
    return {
        "success": True, 
        "message": "Settings updated successfully", 
        "data": user_settings
    }
