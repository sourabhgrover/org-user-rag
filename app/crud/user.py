from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime, date
from bson import ObjectId
from passlib.context import CryptContext

from app.api.v1.models.user import UserCreate, UserInDB, PyObjectId

# Password hashing context
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)

def get_pwd_hash(pwd: str) -> str:
    return pwd_context.hash(pwd)

async def validate_organization_id(db: AsyncDatabase, organization_id: str) -> bool:
    if not ObjectId.is_valid(organization_id):
        return False
    #  await db.organizations.find_one({"_id": ObjectId(organization_id)})
    org = await db.organizations.find_one({"_id": ObjectId(organization_id)})
    return org is not None

async def get_user_by_email(db: AsyncDatabase, email: str) -> UserInDB:
    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def get_user_by_username(db: AsyncDatabase, username: str) -> UserInDB:
    user_doc = await db.users.find_one({"username": username})
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def create_user(db: AsyncDatabase, user_create: UserCreate):
    try:
        # Check if user already exists by email or username
        if await get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user_create.email}' already exists."
            )
        if await get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with username '{user_create.username}' already exists."
            )
        
        # Check if organization exists if organization_id is provided
        if not await validate_organization_id(db, user_create.organization_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with ID '{user_create.organization_id}' does not exist."
            )
    
        user_create_data = user_create.model_dump(by_alias=True)

        
        user_create_data['hashed_password'] = get_pwd_hash(user_create_data.pop('password'))
        
        
        # Validate required fields are present
        # if 'dob' not in user_create_data or user_create_data['dob'] is None:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Date of birth is required"
        #     )
        
        # if 'hashed_password' not in user_create_data or user_create_data['hashed_password'] is None:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Password hashing failed"
        #     )
        
        # Convert organization_id to ObjectId if it's a valid ObjectId string
        user_create_data['organization_id'] = ObjectId(user_create.organization_id)
        
        # Convert date to datetime for MongoDB storage
        # if isinstance(user_create_data['dob'], date):
        user_create_data['dob'] = datetime.combine(user_create_data['dob'], datetime.min.time())

        # Convert enum to string value for MongoDB storage
        # if 'gender' in user_create_data:
        #     gender_value = user_create_data['gender']
        #     if hasattr(gender_value, 'value'):
        #         user_create_data['gender'] = gender_value.value
        #     else:
        #         user_create_data['gender'] = str(gender_value)
        
        # Add timestamps
        user_create_data['created_at'] = datetime.utcnow()
        user_create_data['updated_at'] = datetime.utcnow()
        
        print(f"User create data after conversion: {user_create_data}")
        
        result = await db.users.insert_one(user_create_data)
        new_user = await db.users.find_one({"_id": result.inserted_id})
        
        print(f"Retrieved user from DB: {new_user}")
        
        return UserInDB(**new_user)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while creating user: {str(e)}"
        )
    
async def delete_user_by_id(user_id:PyObjectId,db:AsyncDatabase) -> bool:
        result = await db.users.delete_one({"_id":ObjectId(user_id)});
        return result.deleted_count > 0