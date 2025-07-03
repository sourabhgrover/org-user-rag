from pymongo.asynchronous.database import AsyncDatabase
from app.api.v1.models.user import UserCreate, UserInDB
from datetime import datetime

async def create_user(db: AsyncDatabase,user_create:UserCreate):
    user_create_data = user_create.model_dump(by_alias=True)
    user_create_data['created_at'] = datetime.utcnow()
    user_create_data['updated_at'] = datetime.utcnow()
    result = await db.users.insert_one(user_create_data)
    new_user = await db.users.find_one({"_id": result.inserted_id})

    return UserInDB(**new_user)