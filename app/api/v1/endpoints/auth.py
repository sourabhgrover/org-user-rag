# app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.database import AsyncDatabase
from datetime import timedelta

from app.db.mongodb import get_database
from app.api.v1.models.token import Token
from app.api.v1.models.auth import UserLogin
from app.crud import user as crud_user # Import user CRUD operations
from app.core import security # Import our security utilities

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=Token, summary="Authenticate user and get access token")
async def login_for_access_token(
    data: UserLogin, # Expects username and password in form data
    db: AsyncDatabase = Depends(get_database)
):
    """
    Authenticates a user with username and password, then returns a JWT access token.
    """
    user = await crud_user.get_user_by_username(db, data.username)
    if not user or not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the access token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, # 'sub' (subject) is standard for JWTs
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}