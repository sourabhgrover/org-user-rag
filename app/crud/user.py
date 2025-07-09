from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from app.api.v1.models.user import UserCreate, UserInDB
from datetime import datetime
from bson import ObjectId

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

        # Convert date to datetime for MongoDB compatibility
        # if 'dob' in user_create_data:
        #     user_create_data['dob'] = datetime.combine(user_create_data['dob'], datetime.min.time())
        
        # # Convert enum to string value
        # if 'gender' in user_create_data:
        #     user_create_data['gender'] = user_create_data['gender'].value if hasattr(user_create_data['gender'], 'value') else str(user_create_data['gender'])
        
        # Convert organization_id to ObjectId if it's a valid ObjectId string
        # if 'organization_id' in user_create_data and user_create_data['organization_id'] != 'string':
        #     try:
        #         user_create_data['organization_id'] = ObjectId(user_create_data['organization_id'])
        #     except:
        #         # If invalid ObjectId, keep as string or handle error
        #         pass
        
        # Add timestamps
        user_create_data['created_at'] = datetime.utcnow()
        user_create_data['updated_at'] = datetime.utcnow()
        
        result = await db.users.insert_one(user_create_data)
        new_user = await db.users.find_one({"_id": result.inserted_id})

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