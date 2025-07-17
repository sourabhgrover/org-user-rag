# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.asynchronous.database import AsyncDatabase
from jose import JWTError, ExpiredSignatureError # Import ExpiredSignatureError for specific handling

from app.db.mongodb import get_database
from app.api.v1.models.user import UserInDB # Used when fetching full user object
from app.api.v1.models.token import TokenData # Our updated TokenData model
from app.core import security
from app.crud import user as crud_user

# OAuth2PasswordBearer still used to extract the token from the Authorization header
# tokenUrl still points to your login endpoint (even if it accepts JSON now)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme)
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

    print(f"Token",token)
    
    try:
        payload = security.decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        # Extract data from payload. Pydantic's TokenData handles the field mapping.
        # Use .get() with a default for safety if a claim might be missing.
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        is_admin: bool = payload.get("is_admin", False) # Default to False if not explicitly in token
        
        if not username or not user_id: # Both are crucial for identifying user
            raise credentials_exception
        
        # Return a TokenData object populated directly from the JWT payload
        return TokenData(username=username, user_id=user_id, is_admin=is_admin)
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError: # Catch other JWT errors like invalid signature
        raise credentials_exception

# --- Authorization Dependencies (now leveraging TokenData) ---

async def get_current_active_user(
    # This dependency now gets the TokenData (without a DB hit)
    token_data: TokenData = Depends(get_current_user_from_token),
    # It then conditionally hits the DB if the full UserInDB object is needed
    db: AsyncDatabase = Depends(get_database) # Add db dependency here
) -> UserInDB:
    """
    Fetches the full UserInDB object from the database using the user_id from the token.
    Use this when an endpoint needs the complete and freshest user profile data.
    """
    user = await crud_user.get_user(db, token_data.user_id)
    
    if user is None:
        # This case implies the user_id in the token exists but the user was deleted from DB
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in database (token valid but user removed).")
    
    # If you had an 'is_active' field in your UserInDB model, you would check it here:
    # if not user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account.")
        
    return user

async def get_current_admin_user(
    # First, quickly get basic data from token
    token_data: TokenData = Depends(get_current_user_from_token),
    db: AsyncDatabase = Depends(get_database) # Add db dependency here
) -> TokenData:
    """
    Dependency to ensure the current authenticated user has admin privileges.
    It first checks `is_admin` from the token (fast), then re-verifies from DB for stronger security
    against stale admin statuses.
    """
    print(f"Token",token_data)
    if not token_data.is_admin: # Initial quick check from token
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Admin privileges required."
        )
    
    return token_data
    
    # # Re-fetch full user to ensure `is_admin` is absolutely fresh and user still exists.
    # # This is important for critical admin actions to prevent stale tokens granting access.
    # user = await crud_user.get_user(db, token_data.user_id)
    # if user is None or not user.is_admin: # Double check DB status
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Operation forbidden: Admin privileges required (status potentially changed)."
    #     )
    # return user