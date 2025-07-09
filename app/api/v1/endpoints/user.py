from fastapi import APIRouter , Depends, HTTPException,status
from pymongo.asynchronous.database import AsyncDatabase
from app.db.mongodb import get_database  # Import the get_database function
# from app.api.v1.models import UserCreate   # Import your UserCreate model here

from app.api.v1.models.user import UserCreate
from app.crud import user as crud_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/", summary="Create a new user")
async def create_user_endpoint(user_create: UserCreate, db: AsyncDatabase = Depends(get_database)):
    try:  
        new_user = await crud_user.create_user(db, user_create)
        return new_user
    except Exception as e:
        # This is a catch-all for any other unexpected errors
        print(f"Unexpected Error during user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


@router.get("/", summary="Get all users")
async def get_all_users(db: AsyncDatabase = Depends(get_database)):
        return {}

@router.get("/{user_id}",summary="Get user by ID")
async def get_user_by_id(user_id:str,db:AsyncDatabase = Depends(get_database)):
    return {}

@router.put("/{user_id}",summary="Update user by ID")
async def update_user_by_id(user_id:str,data:dict,db:AsyncDatabase = Depends(get_database)):
    return {}

@router.delete("/${user_id}",summary="Delete user by ID")
async def delete_user_by_id(user_id:str,db:AsyncDatabase= Depends(get_database)):
    return {}