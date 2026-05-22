"""
PESU Academy Dashboard — FastAPI Application

Serves attendance, timetable, results data from scraped PESU Academy data.
Designed for Vercel serverless deployment via Mangum.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

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

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    """Health check endpoint."""
    return {"status": "ok", "service": "pesu-academy-api"}


# Mangum handler for Vercel serverless
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
