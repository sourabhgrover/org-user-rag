from fastapi import APIRouter,Depends,UploadFile,File,Query,HTTPException,status
from typing import List
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.crud.doc import upload_files, getDocsByOrgId
from app.api.v1.models.doc import DocOutput

router = APIRouter(prefix="/doc")

@router.post("/", summary="Upload pdf file")
async def upload_file_ep(
    file: List[UploadFile] = File(...),
    organization_id: str = Query(...),
    db: AsyncDatabase = Depends(get_database)
):
    try:
        result = await upload_files(file, organization_id, db)
        return result
    except HTTPException:
        # Re-raise HTTPExceptions from CRUD layer
        raise
    except Exception as e:
        # This is a catch-all for any other unexpected errors
        print(f"Unexpected Error during file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )

@router.get("/{organization_id}", summary="Get documents by organization ID", response_model=List[DocOutput])
async def get_docs_by_org_id(
    organization_id: str,
    db: AsyncDatabase = Depends(get_database)
):
    try:
        docs = await getDocsByOrgId(organization_id, db)
        return docs
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )