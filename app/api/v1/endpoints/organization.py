from fastapi import APIRouter,Depends,HTTPException,status
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError  # Import DuplicateKeyError and PyMongoError for exception handling
from app.db.mongodb import get_database
from app.api.v1.models import OrganizationCreate,OrganizationResponse,PyObjectId  # Import your OrganizationCreate model here
# from app.crud import create_organization  # Import your create_organization function here
from app.crud import organization as crud_organization   # Import your create_organization function here

router = APIRouter(prefix="/organization", tags=["Organization"])

@router.get("/")
async def get_organization_endpoint():
    return {"message": "Organization endpoint is working!"}

@router.get("/{org_id}", response_model=OrganizationResponse, summary="Get organization by Id")
async def get_organization_by_id_endpoint(org_id: PyObjectId, db: AsyncDatabase = Depends(get_database)):
    org = await crud_organization.get_organization_by_id(db, org_id)
    if not org:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,detail="Organization not found")
    return org 

@router.post("/",status_code=status.HTTP_201_CREATED, summary="Create a new organization")
async def create_organization_endpoint(data: OrganizationCreate,db :  AsyncDatabase = Depends(get_database)):

    # try:
        new_org = await crud_organization.create_organization(db, data)
        
        # This handles the specific case where CRUD returns None due to uniqueness conflict
        if new_org is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with name '{data.name}' already exists."
            )
        
        return new_org

    # # HANDLED IT GLOBALLY AT # # the main.py file
    # # Catch specific PyMongo errors if they indicate something
    # # For example, if you had a unique index on organization_name at the DB level,
    # # and the crud method didn't check it, DuplicateKeyError would be raised here.
    # # We already handle it in CRUD, but this is for demonstrating general error handling.
    # except DuplicateKeyError: # Less likely to hit if CRUD checks first, but good to know
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail=f"An organization with the name '{data.name}' already exists."
    #     )
    # except PyMongoError as e:
    #     # This catches general MongoDB-related errors (connection issues, operation failures etc.)
    #     print(f"MongoDB Error during organization creation: {e}") # Log the error for debugging
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="A database error occurred during organization creation."
    #     )
    # except Exception as e:
    #     # This is a catch-all for any other unexpected errors
    #     print(f"Unexpected Error during organization creation: {e}") # Log the error for debugging
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="An unexpected error occurred."
    #     )