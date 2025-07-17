# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from datetime import timedelta


from app.db.mongodb import get_database
from app.api.v1.models.token import Token
from app.api.v1.models.auth import UserLogin # Assuming you use UserLogin for JSON body
from app.crud import user as crud_user
from app.core import security

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=Token, summary="Authenticate user and get access token")
async def login_for_access_token(
    user_credentials: UserLogin,
    db: AsyncDatabase = Depends(get_database)
):
    """
    Authenticates a user with username and password, then returns a JWT access token.
    The token now includes user_id and is_admin status.
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
    access_token = security.create_access_token(
        data={
            "sub": user.username,          # 'sub' is a standard JWT claim for subject
            "user_id": str(user.id),       # Store user's MongoDB ObjectId as a string
            "is_admin": user.is_admin      # Store admin status
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}