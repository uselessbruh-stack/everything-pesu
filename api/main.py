"""
PESU Academy Dashboard — FastAPI Application

Serves attendance, timetable, results data from scraped PESU Academy data.
Designed for Vercel serverless deployment via Mangum.
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

from .attendance import router as attendance_router
from .auth import router as auth_router
from .results import router as results_router
from .timetable import router as timetable_router
from .user import router as user_router

app = FastAPI(
    title="PESU Academy API",
    description="Backend API for the PESU Academy Attendance Dashboard",
    version="1.0.0",
)

# CORS — allow Vercel preview/production domains + local dev
origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(attendance_router)
app.include_router(timetable_router)
app.include_router(results_router)
app.include_router(user_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler so 500 errors return useful messages instead of blank crashes."""
    tb = traceback.format_exc()
    logger.error(f"Unhandled error on {request.url}: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


@app.get("/")
async def root():
    """API info and available endpoints."""
    return {
        "name": "PESU Academy API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth/login, /api/auth/me, /api/auth/logout",
            "attendance": "/api/attendance/summary, /api/attendance/courses, /api/attendance/course/{code}",
            "timetable": "/api/timetable, /api/timetable/week",
            "results": "/api/results, /api/results/course/{code}",
            "user": "/api/user/profile, /api/user/settings",
            "health": "/api/health",
        },
    }


@app.get("/api/health")
async def health():
    """Health check endpoint with diagnostics."""
    import os
    from pathlib import Path
    from .data_loader import DATA_FILE

    this_file = Path(__file__).resolve()
    candidates = [
        str(this_file.parent.parent / "attendance_data.json"),
        str(this_file.parent / "attendance_data.json"),
        "/var/task/attendance_data.json",
        "/var/task/api/attendance_data.json",
    ]

    return {
        "status": "ok",
        "service": "pesu-academy-api",
        "__file__": str(this_file),
        "cwd": os.getcwd(),
        "data_file": str(DATA_FILE),
        "data_file_exists": DATA_FILE.exists(),
        "candidates": {p: Path(p).exists() for p in candidates},
        "cwd_listing": os.listdir(os.getcwd())[:20],
    }


# Mangum handler for Vercel serverless
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

