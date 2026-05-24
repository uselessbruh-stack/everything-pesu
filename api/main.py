"""
PESU Academy Dashboard — FastAPI Application
Fetches live data from PESU Academy via HTTP scraping.
"""

import logging
import os
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .attendance import router as attendance_router
    from .auth import router as auth_router
    from .results import router as results_router
    from .timetable import router as timetable_router
    from .user import router as user_router
    from .ratings import router as ratings_router
    from .contact import router as contact_router
    from .database import init_db
except ImportError:
    from attendance import router as attendance_router
    from auth import router as auth_router
    from results import router as results_router
    from timetable import router as timetable_router
    from user import router as user_router
    from ratings import router as ratings_router
    from contact import router as contact_router
    from database import init_db

app = FastAPI(
    title="PESU Academy API",
    description="Live data from PESU Academy via HTTP scraping",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(auth_router)
app.include_router(attendance_router)
app.include_router(timetable_router)
app.include_router(results_router)
app.include_router(user_router)
app.include_router(ratings_router)
app.include_router(contact_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"Unhandled error on {request.url}: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


@app.get("/")
async def root():
    return {"name": "PESU Academy API", "version": "2.0.0", "mode": "live"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mode": "live-scraping",
        "service": "pesu-academy-api",
    }


# Mangum handler for Vercel serverless
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
