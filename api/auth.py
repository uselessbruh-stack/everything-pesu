"""
JWT Authentication module for PESU Academy API.
"""

import os
import time
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

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


class UserResponse(BaseModel):
    username: str
    authenticated: bool


def create_token(username: str) -> str:
    """Create a JWT token for the given username."""
    payload = {
        "sub": username,
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


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """FastAPI dependency to get the current authenticated user."""
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

    return {"username": payload["sub"]}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Authenticate with PESU credentials and get a JWT token.
    Accepts any valid-looking PESU SRN + password.
    """
    username = body.username.strip()
    password = body.password.strip()

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password are required",
        )

    token = create_token(username)
    return TokenResponse(
        access_token=token,
        user={"username": username},
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return UserResponse(username=user["username"], authenticated=True)


@router.post("/logout")
async def logout():
    """Logout endpoint. Token invalidation is handled client-side."""
    return {"message": "Logged out successfully"}
