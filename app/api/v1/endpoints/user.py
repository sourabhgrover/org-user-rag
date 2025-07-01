from fastapi import APIRouter
from app.api.v1.models.user import UserCreate  # Import your UserCreate model here

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/",summary="List all users")
async def get_user():
    return {"message": "User endpoint is working!"}

@router.post("/", summary="Create a new user")
async def create_user(
    user_create: UserCreate  # Replace with your actual UserCreate model
):
    return {"message": "User created successfully!"}