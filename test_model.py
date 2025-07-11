# test_models.py

from pydantic import BaseModel,Field,BeforeValidator,EmailStr,field_validator,ConfigDict
from typing import Annotated,Optional
from enum import Enum
from datetime import date,datetime
from bson import ObjectId

# --- PASTE YOUR PyObjectId, GenderEnum, UserBase, UserCreate, UserInDB, UserResponse CLASSES HERE ---
# Make sure to include all your classes exactly as they are in your app/api/v1/models/user.py
# For example:

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
    gender: Annotated[GenderEnum, Field(description="Gender of the user")]
    dob: Annotated[date, Field(description="Date of birth of the user", example="1990-01-15")]
    is_admin: Annotated[bool, Field(default=False, description="Indicates if the user is an admin", example=True)]
    organization_id: Annotated[PyObjectId, Field(alias="organization_id", description="The ID of the organization the user belongs to",example="686a61391e3e8aaa36c09162")]

class UserCreate(UserBase):
    password: Annotated[str,Field(min_length=8, max_length=128, description="Password for the user account",)] 
    pass

class UserInDB(UserBase):
    """Model for users as stored in the database, including MongoDB _id and timestamps."""
    id: PyObjectId = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    hashed_password: Annotated[str, Field(description="Hashed password for the user account")]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)

    # Re-enable your field validators if you want to test them.
    # @field_validator('dob', mode='before')
    # @classmethod
    # def convert_datetime_to_date(cls, v):
    #     if isinstance(v, datetime):
    #         return v.date()
    #     return v

    # @field_validator('gender', mode='before')
    # @classmethod
    # def convert_gender_to_enum(cls, v):
    #     if isinstance(v, str):
    #         return GenderEnum(v)
    #     return v
    
class UserResponse(UserInDB):
    model_config = ConfigDict(exclude={"hashed_password"})

# --- END OF PASTED CLASSES ---


# Sample data mimicking what MongoDB returns after a find_one operation
# Note: MongoDB stores _id as ObjectId, and dates as datetime objects.
sample_mongo_doc = {
    "_id": ObjectId("60d5ec49c6d3b4e3e3c6b2a1"), # A sample ObjectId
    "first_name": "Sample",
    "last_name": "User",
    "email": "sample@example.com",
    "username": "sampleuser",
    "gender": "Male",
    "dob": datetime(1990, 5, 10), # MongoDB often stores dates as datetime
    "is_admin": False,
    "organization_id": ObjectId("686a61391e3e8aaa36c09162"),
    "hashed_password": "this_is_a_secret_hashed_password",
    "created_at": datetime(2023, 1, 1, 10, 0, 0),
    "updated_at": datetime(2023, 1, 1, 10, 0, 0),
}

print("--- Original MongoDB Document (as Python dict) ---")
print(sample_mongo_doc)
print("-" * 50 + "\n")

# 1. Test instantiating UserInDB and dumping it
# This simulates what happens when you do UserInDB(**new_user) in CRUD
try:
    user_in_db_instance = UserInDB(**sample_mongo_doc)
    print("--- UserInDB instance (model_dump()) ---")
    # Expected: 'id' (as string), 'hashed_password' present
    print(user_in_db_instance.model_dump())
    print("-" * 50 + "\n")
except Exception as e:
    print(f"Error creating UserInDB instance: {e}")

# 2. Test instantiating UserResponse directly and dumping it
# This simulates directly converting the MongoDB dict to UserResponse
try:
    user_response_direct_instance = UserResponse(**sample_mongo_doc)
    print("--- UserResponse instance (model_dump()) from raw dict ---")
    # Expected: 'id' (as string), 'hashed_password' ABSENT
    print(user_response_direct_instance.model_dump())
    print("-" * 50 + "\n")
except Exception as e:
    print(f"Error creating UserResponse direct instance: {e}")

# 3. Test converting UserInDB instance to UserResponse output (what FastAPI does)
# This is the most accurate simulation of FastAPI's response_model logic
try:
    # First, create UserInDB from the mongo doc
    user_in_db_for_response_flow = UserInDB(**sample_mongo_doc)

    # Then, simulate FastAPI applying UserResponse to it
    # FastAPI does an internal conversion that respects the target model's config
    # We can approximate this by creating UserResponse from the UserInDB's model_dump()
    # or by explicitly converting
    final_api_response_dict = UserResponse.model_validate(user_in_db_for_response_flow.model_dump()).model_dump()
    
    print("--- Simulated FastAPI Response (UserInDB -> UserResponse) ---")
    # Expected: 'id' (as string), 'hashed_password' ABSENT
    print(final_api_response_dict)
    print("-" * 50 + "\n")

except Exception as e:
    print(f"Error simulating FastAPI response: {e}")