from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.core.auth import create_access_token
from app.core.security import verify_password
from app.dependencies import get_current_user
from app.schemas.routers import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if body.email != settings.admin_email or not verify_password(
        body.password, settings.admin_password
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(body.email))


@router.get("/me")
async def me(current_user: str = Depends(get_current_user)):
    return {"email": current_user}
