from pydantic import BaseModel,  Field

class UserBase(BaseModel):
    firstname: str = Field(..., description="The user's first name")
    lastname: str = Field(..., description="The user's last name")

class UserCreate(UserBase):
    # Inherits all fields from UserBase
    pass