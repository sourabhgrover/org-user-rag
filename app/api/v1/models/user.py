from pydantic import BaseModel,Field,BeforeValidator,EmailStr,field_validator
from typing import Annotated,Optional
from enum import Enum
from datetime import date,datetime
from bson import ObjectId  # For MongoDB's native ObjectId

# Custom type for ObjectId handling in Pydantic
PyObjectId = Annotated[str, BeforeValidator(str)]

class GenderEnum(str,Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class UserBase(BaseModel):
    first_name: Annotated[str, Field(min_length=3, max_length=50,description="The first name of the user", example="Sourabh")]
    last_name: Annotated[str, Field(min_length=3, max_length=50,description="The last name of the user", example="Grover")]
    email: Annotated[EmailStr, Field(description="The email address of the user", example="abc@xyx.com")]
    username: Annotated[str, Field(min_length=3, max_length=50, description="The username of the user", example="sourabhgrover")]
    # gender: Annotated[GenderEnum, Field(description="Gender of the user")]
    # dob: Annotated[date, Field(description="Date of birth of the user", example="1990-01-15")]
    # is_admin: Annotated[bool, Field(default=False, description="Indicates if the user is an admin", example=True)]
    organization_id: Annotated[PyObjectId, Field(alias="organization_id", description="The ID of the organization the user belongs to")]

class UserCreate(UserBase):
    # password: Annotated[str,Field(min_length=8, max_length=128, description="Password for the user account",)] 
    pass

class UserInDB(UserBase):
    """Model for users as stored in the database, including MongoDB _id and timestamps."""
    id: PyObjectId = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    # hashed_password: Annotated[str, Field(description="Hashed password for the user account")]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # @field_validator('dob', mode='before')
    # @classmethod
    # def convert_datetime_to_date(cls, v):
    #     """Convert datetime back to date if it comes from MongoDB as datetime"""
    #     if isinstance(v, datetime):
    #         return v.date()
    #     return v

    # @field_validator('gender', mode='before')
    # @classmethod
    # def convert_gender_to_enum(cls, v):
    #     """Convert string back to enum if it comes from MongoDB as string"""
    #     if isinstance(v, str):
    #         return GenderEnum(v)
    #     return v