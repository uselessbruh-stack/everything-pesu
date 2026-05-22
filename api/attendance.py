from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import math
from api.auth import verify_jwt_token
from api.config import settings, cache
from api.data_store import load_raw_data, generate_class_history, scrape_data_async

router = APIRouter(prefix="/api/attendance", tags=["attendance"])

# --- Request / Response Models ---
class CalculateRequest(BaseModel):
    course_code: Optional[str] = None
    current_attended: int
    current_total: int
    target_percentage: float = 85.0
    classes_to_add: Optional[int] = 0
    scenario: Optional[str] = "attend"  # "attend" or "bunk"
    classes_count: Optional[int] = 0

class CalculateResponse(BaseModel):
    scenario_type: str
    classes_to_process: int
    new_attended: int
    new_total: int
    new_percentage: float
    meets_target: bool
    required_to_target: int
    can_safely_bunk: int
    warning: Optional[str] = None

# --- Helper Functions ---
def compute_what_if_stats(attended: int, total: int, target: float) -> Dict[str, Any]:
    """Calculates required classes and safe bunks for a target"""
    if total == 0:
        return {"required": 0, "can_bunk": 0, "on_track": True}
        
    current_pct = (attended / total) * 100
    
    # 1. Classes needed to reach target: (attended + X) / (total + X) = target / 100
    # X = (target * total - attended * 100) / (100 - target)
    if current_pct >= target:
        classes_needed = 0
    else:
        num = (target * total) - (attended * 100)
        den = 100 - target
        classes_needed = math.ceil(num / den) if den > 0 else 0
        classes_needed = max(0, classes_needed)
        
    # 2. Classes safe to bunk: attended / (total + Y) = target / 100
    # Y = (attended * 100) / target - total
    if current_pct < target:
        can_bunk = 0
    else:
        if target > 0:
            val = (attended * 100) / target
            can_bunk = math.floor(val - total)
            can_bunk = max(0, can_bunk)
        else:
            can_bunk = 0
            
    return {
        "required": classes_needed,
        "can_bunk": can_bunk,
        "on_track": current_pct >= target
    }

# --- Routes ---

@router.get("/summary")
async def get_summary(current_user: dict = Depends(verify_jwt_token)):
    """
    Get overall attendance summary.
    Result is cached for 5 minutes.
    """
    username = current_user["username"]
    cache_key = f"summary:{username}"
    
    # Try cache first
    cached_summary = cache.get(cache_key)
    if cached_summary:
        return {"success": True, "data": cached_summary, "cached": True}
        
    # Load raw data
    data = load_raw_data()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance records found"
        )
        
    summary = data.get("summary", {})
    
    # Cache and return
    cache.set(cache_key, summary, settings.CACHE_TTL["summary"])
    return {"success": True, "data": summary, "cached": False}

@router.get("/courses")
async def get_courses(current_user: dict = Depends(verify_jwt_token)):
    """
    Get course-wise attendance details.
    Result is cached for 30 minutes.
    """
    username = current_user["username"]
    cache_key = f"courses:{username}"
    
    cached_courses = cache.get(cache_key)
    if cached_courses:
        return {"success": True, "data": cached_courses, "cached": True}
        
    data = load_raw_data()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No course records found"
        )
        
    courses = data.get("courses", [])
    
    cache.set(cache_key, courses, settings.CACHE_TTL["courses"])
    return {"success": True, "data": courses, "cached": False}

@router.get("/course/{course_code}")
async def get_course_detail(course_code: str, current_user: dict = Depends(verify_jwt_token)):
    """
    Get detailed breakdown of a single course.
    Includes class list history, bunk allowance, and targets.
    """
    data = load_raw_data()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No records found"
        )
        
    courses = data.get("courses", [])
    course = next((c for c in courses if c["course_code"].upper() == course_code.upper()), None)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code {course_code} not found"
        )
        
    attended = course["attendance"]["attended"]
    total = course["attendance"]["total"]
    
    # Generate realistic class history
    classes = generate_class_history(course_code, attended, total)
    
    # Compute bunk stats for 85% (default) target
    bunk_stats = compute_what_if_stats(attended, total, 85.0)
    
    detailed_course = {
        **course,
        "classes": classes,
        "bunk_allowance": bunk_stats["can_bunk"],
        "required_attendance": bunk_stats["required"],
        "on_track": bunk_stats["on_track"]
    }
    
    return {"success": True, "data": detailed_course}

@router.post("/sync")
async def sync_attendance(current_user: dict = Depends(verify_jwt_token)):
    """
    Clears cache and scrapes fresh data from PESU Academy.
    Falls back to mock data reload if scraping fails.
    """
    username = current_user["username"]
    
    # Invalidate cache
    cache.delete(f"summary:{username}")
    cache.delete(f"courses:{username}")
    
    # Run async scraping process (with mock fallback)
    data = await scrape_data_async(username, "Mymosi@132513") # Fallback password
    if not data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synchronize attendance data"
        )
        
    return {"success": True, "message": "Attendance data synchronized successfully"}

@router.post("/calculate", response_model=CalculateResponse)
async def calculate_attendance(req: CalculateRequest):
    """
    Calculates various attendance scenarios.
    Useful for 'what-if' bunk and attend predictions.
    """
    # Align classes to evaluate based on inputs
    classes_count = req.classes_count if req.classes_count else req.classes_to_add or 0
    scenario = req.scenario.lower() if req.scenario else "attend"
    
    current_attended = req.current_attended
    current_total = req.current_total
    target = req.target_percentage
    
    if current_total < 0 or current_attended < 0 or current_attended > current_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid attendance counts provided"
        )
        
    if scenario == "attend":
        new_attended = current_attended + classes_count
        new_total = current_total + classes_count
    elif scenario == "bunk":
        new_attended = current_attended
        new_total = current_total + classes_count
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scenario must be 'attend' or 'bunk'"
        )
        
    new_percentage = (new_attended / new_total * 100) if new_total > 0 else 0.0
    meets_target = new_percentage >= target
    
    # Calculate required and safety stats for this course state
    stats = compute_what_if_stats(current_attended, current_total, target)
    
    warning = None
    if scenario == "bunk" and not meets_target:
        warning = f"Bunking {classes_count} classes will drop your attendance below the {target}% target!"
        
    return CalculateResponse(
        scenario_type=scenario,
        classes_to_process=classes_count,
        new_attended=new_attended,
        new_total=new_total,
        new_percentage=round(new_percentage, 2),
        meets_target=meets_target,
        required_to_target=stats["required"],
        can_safely_bunk=stats["can_bunk"],
        warning=warning
    )
