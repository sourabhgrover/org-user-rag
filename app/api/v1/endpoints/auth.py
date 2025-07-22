# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from datetime import timedelta

from app.db.mongodb import get_database
from app.api.v1.models.token import Token
from app.api.v1.models.auth import UserLogin, AuthResponse
from app.api.v1.models.response import StandardResponse
from app.crud import user as crud_user
from app.core import security

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=StandardResponse[AuthResponse], summary="Authenticate user and get access token")
async def login_for_access_token(
    user_credentials: UserLogin,
    db: AsyncDatabase = Depends(get_database)
):
    """
    Authenticates a user with username and password, then returns a JWT access token along with user information.
    The token includes user_id and is_admin status.
    """
    user = await crud_user.get_user_by_username(db, user_credentials.username)
    if not user or not security.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Define token expiration
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create the access token payload with user_id and is_admin
    token = security.create_access_token(
        data={
            "sub": user.username,          # 'sub' is a standard JWT claim for subject
            "user_id": str(user.id),       # Store user's MongoDB ObjectId as a string
            "is_admin": user.is_admin      # Store admin status
        },
        expires_delta=access_token_expires
    )
    
    # Prepare the result data
    result = {
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "gender": user.gender,
            "dob": user.dob.isoformat() if user.dob else None,
            "is_admin": user.is_admin,
            "organization_id": str(user.organization_id),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        },
        "token": token
    }
    
    return StandardResponse(
        status="success",
        message="User authenticated successfully",
        data=result
    )