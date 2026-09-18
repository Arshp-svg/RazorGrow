from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.auth_dependencies import get_current_user
from app.models.models import User
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    refresh_access_token,
    revoke_refresh_token,
    
)
from app.db.database import SessionLocal
from app.schemas.auth import (
    RegisterRequest,
    UserResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
)

from app.services.auth_service import (
    register_user,
    authenticate_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            email=str(request.email),
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
    )
    
@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db,
            email=str(request.email),
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(db, user.id)

    return LoginResponse(
    access_token=access_token,
    refresh_token=refresh_token,
    token_type="bearer",
    user=UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
    ),
)
    
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
    )
    
@router.post("/refresh")
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    try:
        access_token = refresh_access_token(db, request.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
    
@router.post("/logout")
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    try:
        revoke_refresh_token(db, request.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return {"message": "Logged out successfully"}