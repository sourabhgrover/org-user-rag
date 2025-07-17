from fastapi import APIRouter , Depends, HTTPException,status,Query
from pymongo.asynchronous.database import AsyncDatabase
from typing import Optional
from app.db.mongodb import get_database  # Import the get_database function
from app.api.v1.models.user import UserCreate, PyObjectId,UserResponse,UserUpdate
from app.crud import user as crud_user
from app.core.dependencies import get_current_admin_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/",response_model=UserResponse, summary="Create a new user",dependencies=[Depends(get_current_admin_user)])
async def create_user_endpoint(user_create: UserCreate, db: AsyncDatabase = Depends(get_database)):
    try:  
        new_user = await crud_user.create_user(db, user_create)
        return new_user
    except HTTPException:
        # Re-raise HTTPExceptions from CRUD layer (like duplicate email errors)
        raise
    except Exception as e:
        # This is a catch-all for any other unexpected errors
        print(f"Unexpected Error during user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


@router.get("/", summary="Get all users")
async def get_all_users(skip:int = Query(0,ge=0),limit:int = Query(100,le=1000),search_name:Optional[str] = Query(None,description='Search user by name case insesnitive'),db: AsyncDatabase = Depends(get_database)):
        users = await crud_user.get_all_user(skip,limit,search_name,db)
        return users

@router.get("/{user_id}",summary="Get user by ID")
async def get_user_by_id(user_id:PyObjectId,db:AsyncDatabase = Depends(get_database)):
    try:
        user = await crud_user.get_user_by_id(user_id, db)
        return user
    except HTTPException:
        # Re-raise HTTPExceptions from CRUD layer (like user not found)
        raise
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="A unexpected error occur {e}")

@router.put("/{user_id}",summary="Update user by ID")
async def update_user_by_id(user_id:str,update_data:UserUpdate,db:AsyncDatabase = Depends(get_database)):
    try:
        updated_user = await crud_user.update_user_by_id(user_id,update_data,db)
        return updated_user
    except HTTPException:
        # Re-raise HTTPExceptions from CRUD layer 
        raise
    
    except HTTPException as e:
     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="An unexpected error occurred.")


@router.delete("/${user_id}",summary="Delete user by ID")
async def delete_user_by_id(user_id:PyObjectId,db:AsyncDatabase= Depends(get_database)):
    result = await crud_user.delete_user_by_id(user_id,db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

    return {"detail":"User deleted successfully"}