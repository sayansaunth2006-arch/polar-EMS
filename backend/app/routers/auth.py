from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate(session: Session, email: str, password: str) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None or not verify_password(password, user.hashed_password) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return user


@router.post("/login", response_model=TokenResponse)
def login_json(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """JSON login used by the frontend."""
    user = _authenticate(session, payload.email, payload.password)
    token = create_access_token(subject=user.email, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, full_name=user.full_name)


@router.post("/token", response_model=TokenResponse)
def login_oauth2_form(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> TokenResponse:
    """OAuth2-compatible form login, e.g. for the interactive /docs Authorize button."""
    user = _authenticate(session, form_data.username, form_data.password)
    token = create_access_token(subject=user.email, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, full_name=user.full_name)


@router.get("/me", response_model=UserOut)
def read_current_user(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role.value, station_id=user.station_id)
