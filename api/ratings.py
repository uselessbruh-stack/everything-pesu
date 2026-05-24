from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional
import logging
from .database import add_rating, get_rating_stats

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ratings",
    tags=["ratings"],
)

class RatingSubmit(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=500, description="Optional text feedback")

    @validator('rating')
    def validate_rating(cls, v):
        if v not in [1, 2, 3, 4, 5]:
            raise ValueError("Rating must be a whole number between 1 and 5")
        return v

@router.get("")
async def fetch_ratings_summary():
    """Retrieves the aggregate rating stats (average score and total count)."""
    try:
        stats = await get_rating_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching ratings summary: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve ratings statistics")

@router.post("")
async def submit_rating(payload: RatingSubmit):
    """Submits a new rating and returns the updated metrics."""
    try:
        updated_stats = await add_rating(
            rating=payload.rating,
            comment=payload.comment
        )
        return {
            "status": "success",
            "message": "Thank you for your rating!",
            "ratings": updated_stats
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error submitting rating: {e}")
        raise HTTPException(status_code=500, detail="Could not submit rating. Please try again.")
