from pydantic import BaseModel, Field
from typing import Optional

class Token(BaseModel):
    """Model for the returned JWT token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: str
    user_id: str = Field(alias="user_id") # Use alias to match 'user_id' in JWT payload
    is_admin: bool