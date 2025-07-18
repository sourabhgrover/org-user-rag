# app/dependencies.py
from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer # REMOVE THIS LINE
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # ADD THESE IMPORTS
from pymongo.asynchronous.database import AsyncDatabase
from jose import JWTError, ExpiredSignatureError

from app.db.mongodb import get_database
from app.api.v1.models.user import UserInDB
from app.api.v1.models.token import TokenData
from app.core import security
from app.crud import user as crud_user

# Replace OAuth2PasswordBearer with HTTPBearer
# This simply tells FastAPI/Swagger UI to expect a Bearer token in the Authorization header.
# It does NOT involve a 'tokenUrl' as this scheme doesn't define how to GET the token.
bearer_scheme = HTTPBearer() # Renamed from oauth2_scheme for clarity

async def get_current_user_from_token(
    # The dependency now receives HTTPAuthorizationCredentials
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TokenData:
    """
    Dependency to get essential user data directly from the JWT payload.
    This does NOT hit the database for every request, making it very fast.
    Raises HTTPException if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Access the token string from credentials.credentials
        token = credentials.credentials 
        payload = security.decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        is_admin: bool = payload.get("is_admin", False)
        
        if not username or not user_id:
            raise credentials_exception
        
        return TokenData(username=username, user_id=user_id, is_admin=is_admin)
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

# --- Authorization Dependencies (no change in logic, just input dependency) ---

async def get_current_active_user(
    # This dependency now consumes the TokenData from the updated get_current_user_from_token
    token_data: TokenData = Depends(get_current_user_from_token),
    db: AsyncDatabase = Depends(get_database)
) -> UserInDB:
    """
    Fetches the full UserInDB object from the database using the user_id from the token.
    Use this when an endpoint needs the complete and freshest user profile data.
    This dependency WILL hit the database.
    """
    user = await crud_user.get_user(db, token_data.user_id)
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in database (token valid but user removed).")
    
    return user

async def get_current_admin_user(
    token_data: TokenData = Depends(get_current_user_from_token)
) -> TokenData:
    """
    Dependency to ensure the current authenticated user has admin privileges.
    This version relies *solely* on the 'is_admin' flag stored in the JWT payload
    and does NOT perform an additional database lookup for freshness.
    """
    if not token_data.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Admin privileges required."
        )
    return token_data