from fastapi import APIRouter,Depends,HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from app.db.mongodb import get_database
from app.api.v1.models import OrganizationCreate  # Import your OrganizationCreate model here
from app.crud import create_organization  # Import your create_organization function here

router = APIRouter(prefix="/organization", tags=["Organization"])

@router.get("/")
async def get_organization():
    return {"message": "Organization endpoint is working!"}


@router.post("/", summary="Create a new organization")
async def create_organization_endpoint(data: OrganizationCreate,db :  AsyncDatabase = Depends(get_database)):

    org = await create_organization(db, data)
    if not org:
        raise HTTPException(status_code=500, detail="Organization could not be created due to a database error.")
    return org