from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime, date
from bson import ObjectId
from passlib.context import CryptContext

from app.api.v1.models.user import UserCreate, UserInDB, PyObjectId,UserResponse,UserUpdate

# Password hashing context
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    # Ensure plain_pwd is bytes for comparison if hashed_pwd was stored as bytes
    # However, passlib's verify method typically handles this if hash() also produces string
    return pwd_context.verify(plain_pwd, hashed_pwd)

def get_pwd_hash(pwd: str) -> str:
    # Passlib's hash() method for bcrypt expects bytes for input
    # and returns a string (the hashed password)
    # The .decode('utf-8') was incorrect because the output is already a string.
    return pwd_context.hash(pwd.encode('utf-8')) # <-- REMOVED .decode('utf-8') HERE

# ... (rest of your crud.py file) ...

async def validate_organization_id(db: AsyncDatabase, organization_id: str) -> bool:
    if not ObjectId.is_valid(organization_id):
        return False
    org = await db.organizations.find_one({"_id": ObjectId(organization_id)})
    return org is not None

async def get_user_by_email(db: AsyncDatabase, email: str) -> UserInDB:
    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        # Debugging: Print user_doc before Pydantic conversion
        print(f"get_user_by_email: Retrieved user_doc: {user_doc}")
        return UserInDB(**user_doc)
    return None

async def get_user_by_username(db: AsyncDatabase, username: str) -> UserInDB:
    user_doc = await db.users.find_one({"username": username})
    if user_doc:
        # Debugging: Print user_doc before Pydantic conversion
        print(f"get_user_by_username: Retrieved user_doc: {user_doc}")
        return UserInDB(**user_doc)
    return None

async def create_user(db: AsyncDatabase, user_create: UserCreate):
    try:
        # Debugging: Print initial user_create object
        print(f"create_user: Initial user_create: {user_create}")

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
        
        # Convert Pydantic model to dictionary for MongoDB insertion
        # by_alias=True ensures _id is used for 'id' field
        user_create_data = user_create.model_dump(by_alias=True)

        # Debugging: Print data after initial model_dump
        print(f"create_user: Data after model_dump: {user_create_data}")

        # Hash password and remove plain password
        # Ensure get_pwd_hash correctly handles encoding/decoding
        user_create_data['hashed_password'] = get_pwd_hash(user_create_data.pop('password'))
        
        # Convert organization_id to ObjectId for MongoDB
        user_create_data['organization_id'] = ObjectId(user_create.organization_id)
        
        # Convert date to datetime for MongoDB storage
        # user_create_data['dob'] is already a date object from UserCreate
        user_create_data['dob'] = datetime.combine(user_create_data['dob'], datetime.min.time())

        # Ensure gender enum is stored as string
        if 'gender' in user_create_data and hasattr(user_create_data['gender'], 'value'):
            user_create_data['gender'] = user_create_data['gender'].value
        
        # Add timestamps
        user_create_data['created_at'] = datetime.utcnow()
        user_create_data['updated_at'] = datetime.utcnow()
        
        # Debugging: Print final data before insertion
        print(f"create_user: Data before insert_one: {user_create_data}")
        
        result = await db.users.insert_one(user_create_data)
        
        # Debugging: Print inserted_id
        print(f"create_user: Inserted ID: {result.inserted_id}")

        new_user = await db.users.find_one({"_id": result.inserted_id})
        
        # Debugging: Print retrieved user from DB
        print(f"create_user: Retrieved user from DB: {new_user}")
        
        # This is where the Pydantic validation error occurs if new_user is missing fields
        
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


async def update_user_by_id(user_id:PyObjectId,update_data:UserUpdate,db:AsyncDatabase):
        
        user = await get_user_by_id(user_id,db)
        if not user:
            return None
        

        # 2. Convert Pydantic model to a dictionary, removing None values
        #    exclude_none=True ensures only fields provided by the client are included in update_data
        #    by_alias=True handles organization_id if its alias is used
        update_data_dict = update_data.model_dump(exclude_none=True,by_alias=True)
        
        if 'dob' in update_data_dict and isinstance(update_data_dict['dob'], date):
            update_data_dict['dob'] = datetime.combine(update_data_dict['dob'], datetime.min.time())

        update_data_dict["updated_at"] = datetime.utcnow()

         # If no fields were provided for update (after stripping None values)
        if not update_data_dict:
            return None # Indicate no actual changes to apply
        
        # Perfrom update operation
        result = await db.users.update_one(
            {'_id':ObjectId(user_id)},
            {'$set':update_data_dict}
        )
        
        # Check if data is modified
        if result.modified_count == 1:
            return await get_user_by_id(user_id,db)
        
        return None


async def get_user_by_id(user_id:PyObjectId,db:AsyncDatabase):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid User Id")
    
    user = await db.users.find_one({'_id':ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Details not found")
    return UserInDB(**user)

async def get_all_user(skip,limit,search_name,db):
    query_filter = {}
    if search_name:
        query_filter['first_name'] = {"$regex":search_name,"$options":"i"}

    cursor = db.users.find(query_filter).skip(skip).limit(limit)
    print(f"cursor: {cursor}")  # Debugging: Print the cursor object
    users = await cursor.to_list(length=limit)
    return [UserInDB(**user) for user in users]