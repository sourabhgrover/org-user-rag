# app/api/v1/models/token.py

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Model for the returned JWT token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Model for the data contained within the JWT token."""
    username: Optional[str] = None # Or user_id: Optional[str] = None