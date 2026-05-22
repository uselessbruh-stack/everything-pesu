from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from api.auth import verify_jwt_token
from api.config import settings, cache
from api.data_store import load_raw_data

router = APIRouter(prefix="/api/results", tags=["results"])

@router.get("")
async def get_all_results(current_user: dict = Depends(verify_jwt_token)):
    """
    Get exam and assignment results.
    Cached for 1 hour.
    """
    username = current_user["username"]
    cache_key = f"results:{username}"
    
    cached_results = cache.get(cache_key)
    if cached_results:
        return {"success": True, "data": cached_results, "cached": True}
        
    data = load_raw_data()
    if not data:
        raise HTTPException(status_code=404, detail="No results found")
        
    results = data.get("results", {})
    
    cache.set(cache_key, results, settings.CACHE_TTL["results"])
    return {"success": True, "data": results, "cached": False}

@router.get("/course/{course_code}")
async def get_course_results(course_code: str, current_user: dict = Depends(verify_jwt_token)):
    """Get exam results for a specific course code"""
    data = load_raw_data()
    if not data:
        raise HTTPException(status_code=404, detail="No records found")
        
    results = data.get("results", {})
    
    course_results = {}
    for sem_name, sem_data in results.items():
        courses = sem_data.get("courses", [])
        course = next((c for c in courses if c["course_code"].upper() == course_code.upper()), None)
        if course:
            course_results = {
                "semester": sem_name,
                "course_code": course["course_code"],
                "course_name": course["course_name"],
                "assessments": course.get("assessments", {}),
                "marks": course.get("marks", {})
            }
            break
            
    if not course_results:
        raise HTTPException(
            status_code=404, 
            detail=f"No results found for course {course_code}"
        )
        
    return {"success": True, "data": course_results}
