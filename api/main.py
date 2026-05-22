from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.config import settings
from api.auth import router as auth_router
from api.attendance import router as attendance_router
from api.timetable import router as timetable_router
from api.results import router as results_router
from api.user import router as user_router

# Initialize FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description="Full-stack FastAPI server for the PESU Academy Dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

# Health Check & Root Endpoints
@app.get("/")
async def root():
    return {
        "name": settings.API_TITLE,
        "status": "online",
        "documentation": "/api/docs",
        "endpoints": {
            "auth": "/api/auth",
            "attendance": "/api/attendance",
            "timetable": "/api/timetable",
            "results": "/api/results",
            "user": "/api/user"
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2026-05-22T04:26:17Z",
        "cache": "active"
    }

# Vercel serverless adapter
handler = Mangum(app)
