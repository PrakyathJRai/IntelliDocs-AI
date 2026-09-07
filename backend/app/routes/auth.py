from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app.models.user import User

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse
)
from app.services.auth_service import (
    hash_password,
    verify_password
)
from app.services.jwt_service import (
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=RegisterResponse
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered."
        )

    user = User(
        email=request.email,
        password_hash=hash_password(
            request.password
        )
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        message="User registered successfully.",
        user_id=user.id,
        email=user.email
    )


@router.post(
    "/login",
    response_model=LoginResponse
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    password_valid = verify_password(
        request.password,
        user.password_hash
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        user.id
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer"
    )
@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "user_id": current_user.id,
        "email": current_user.email
    }
