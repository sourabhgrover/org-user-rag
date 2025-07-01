from fastapi import APIRouter

router = APIRouter(prefix="/organization", tags=["Organization"])

@router.get("/")
async def get_organization():
    return {"message": "Organization endpoint is working!"}