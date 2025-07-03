from pydantic import BaseModel,  Field , BeforeValidator
from typing import Annotated
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserBase(BaseModel):
    firstname: str = Field(..., description="The user's first name", min_length=1)
    lastname: str = Field(..., description="The user's last name", min_length=1)

class UserCreate(UserBase):
    # Inherits all fields from UserBase
    pass

class UserInDB(UserBase):
    """Model for users as stored in the database, including MongoDB _id and timestamps."""
    id: PyObjectId = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)