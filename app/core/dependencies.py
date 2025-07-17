# app/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import AsyncDatabase
from jose import JWTError

from app.db.mongodb import get_database
from app.api.v1.models.user import UserInDB
from app.api.v1.models.token import TokenData
from app.core import security # Import our security utilities
from app.crud import user as crud_user # Import user CRUD operations

# OAuth2PasswordBearer is used to extract the token from the Authorization header
# tokenUrl points to the endpoint where clients can get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

async def get_current_user(
    db: AsyncDatabase = Depends(get_database),
    token: str = Depends(oauth2_scheme) # FastAPI will look for 'Bearer <token>' in Authorization header
) -> UserInDB:
    """
    Dependency to get the current authenticated user from the JWT.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decode and verify the token
    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # 2. Extract username from token data
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    token_data = TokenData(username=username)

    # 3. Fetch user from database using username
    user = await crud_user.get_user_by_username(db, token_data.username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Dependency to ensure the current authenticated user is active (not currently used 'is_active').
    You could add a field like 'is_active' to UserInDB and check it here.
    """
    # if not current_user.is_active: # Example if you had an is_active field
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """
    Dependency to ensure the current authenticated user has admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Admin privileges required."
        )
    return current_user