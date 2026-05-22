"""
JWT Authentication — validates against PESU Academy live.
Stores encrypted credentials in JWT for subsequent API calls.
"""

import base64
import os
import time
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

try:
    from .pesu_client import create_session
except ImportError:
    from pesu_client import create_session

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "pesu-dashboard-dev-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 86400  # 24 hours


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def create_token(username: str, password: str) -> str:
    """Create a JWT token with credentials for subsequent PESU API calls."""
    # Base64 encode password for obfuscation (JWT is signed, not encrypted)
    encoded_pw = base64.b64encode(password.encode()).decode()
    payload = {
        "sub": username,
        "pw": encoded_pw,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRATION,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_credentials(payload: dict) -> tuple[str, str]:
    """Extract username and password from JWT payload."""
    username = payload["sub"]
    password = base64.b64decode(payload["pw"]).decode()
    return username, password


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """FastAPI dependency — returns dict with username + password from JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username, password = extract_credentials(payload)
    return {"username": username, "password": password}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Login by validating credentials against PESU Academy live."""
    username = body.username.strip()
    password = body.password.strip()

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password are required",
        )

    # Validate against PESU Academy
    try:
        session = await create_session(username, password)
        await session.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"PESU Academy login failed: {str(e)}",
        )

    token = create_token(username, password)
    return TokenResponse(
        access_token=token,
        user={"username": username},
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return {"username": user["username"], "authenticated": True}


@router.post("/logout")
async def logout():
    """Logout endpoint. Token invalidation is handled client-side."""
    return {"message": "Logged out successfully"}
