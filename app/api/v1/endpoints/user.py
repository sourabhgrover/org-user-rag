from fastapi import APIRouter , Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from app.db.mongodb import get_database  # Import the get_database function
# from app.api.v1.models import UserCreate   # Import your UserCreate model here

from app.api.v1.models.user import UserCreate
from app.crud import create_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/", summary="Create a new user")
async def create_user_endpoint(user_create: UserCreate,db : AsyncDatabase = Depends(get_database)):
    new_user = await create_user(db, user_create)
    if not new_user:
        raise HTTPException(status_code=500, detail="User could not be created due to a database error.")
    return new_user
