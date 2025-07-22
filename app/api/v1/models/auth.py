from pydantic import BaseModel,Field
from typing import Annotated

class UserLogin(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50, description="The username of the user", example="sourabhgrover")]
    password: Annotated[str,Field(min_length=8, max_length=128, description="Password for the user account",example="johndoe")] 

class AuthResponse(BaseModel):
    """Model for authentication response containing user info and token"""
    user: dict  # We'll use dict since we'll be constructing it manually
    token: str 