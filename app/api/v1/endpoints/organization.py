from fastapi import APIRouter,Depends,HTTPException,status,Query
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError  # Import DuplicateKeyError and PyMongoError for exception handling
from typing import List, Optional
from app.db.mongodb import get_database
from app.api.v1.models import OrganizationCreate,OrganizationResponse,PyObjectId,OrganizationUpdate,StandardResponse
# from app.crud import create_organization  # Import your create_organization function here
from app.crud import organization as crud_organization   # Import your create_organization function here

router = APIRouter(prefix="/organization", tags=["Organization"])



@router.get("/{org_id}", response_model=OrganizationResponse, summary="Get organization by Id")
async def get_organization_by_id_endpoint(org_id: PyObjectId, db: AsyncDatabase = Depends(get_database)):
    org = await crud_organization.get_organization_by_id(db, org_id)
    if not org:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,detail="Organization not found")
    return org 

@router.post("/",status_code=status.HTTP_201_CREATED,response_model=StandardResponse[OrganizationResponse], summary="Create a new organization")
async def create_organization_endpoint(data: OrganizationCreate,db :  AsyncDatabase = Depends(get_database)):

    # try:
        new_org = await crud_organization.create_organization(db, data)
        
        # This handles the specific case where CRUD returns None due to uniqueness conflict
        if new_org is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with name '{data.name}' already exists."
            )
        
        return StandardResponse(
            status="success",
            message="Org created successfully",
            data=new_org
        )
        # return new_org

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
"""
@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an organization by Id")
async def delete_organization_endpoint(org_id: PyObjectId, db: AsyncDatabase = Depends(get_database)):
     deleted = await crud_organization.delete_organization_by_id(db, org_id)
     if not deleted:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail="Organization not found"
         )
     return {"detail": "Organization deleted successfully"}

@router.put("/{org_id}", response_model=OrganizationResponse, summary="Update an organization by Id")
async def update_organization_endpoint(org_id: PyObjectId, data: OrganizationUpdate, db: AsyncDatabase = Depends(get_database)):
    # Update the organization data
    updated_org = await crud_organization.update_organization(db, org_id, data)
    
    return updated_org
"""

@router.get(
    "/",
    response_model=List[OrganizationResponse],
    summary="List all organizations"
)
async def list_organizations_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search_name: Optional[str] = Query(None, description="Search by organization name (case-insensitive)"),
    db: AsyncDatabase = Depends(get_database)
):
    """
    Lists all organizations with optional filtering by name and pagination.
    """
    organizations = await crud_organization.get_organizations(
        db,
        skip=skip,
        limit=limit,
        search_name=search_name
    )
    return organizations