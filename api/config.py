import os
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, Tuple

class Settings:
    API_TITLE: str = "PESU Academy Dashboard API"
    JWT_SECRET: str = os.getenv("JWT_SECRET", "pesu-academy-super-secret-key-2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS setup
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://everything-pesu.vercel.app",
        "*"
    ]
    
    # Cache TTLs in seconds
    CACHE_TTL = {
        "summary": 300,      # 5 minutes
        "courses": 1800,     # 30 minutes
        "timetable": 3600,   # 1 hour
        "results": 3600      # 1 hour
    }

settings = Settings()

class CacheManager:
    """In-memory cache manager with TTL support"""
    def __init__(self):
        # Format: {key: (data, expiry_datetime)}
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, expiry = self._cache[key]
            if datetime.now() < expiry:
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        self._cache[key] = (value, expiry)
        
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            
    def clear(self):
        self._cache.clear()

# Global cache instance
cache = CacheManager()
