from fastapi import APIRouter,Depends,UploadFile,File,Query,HTTPException,status
from typing import List
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.crud.doc import upload_files, getDocsByOrgId
from app.api.v1.models.doc import DocOutput
from app.api.v1.models.response import StandardResponse

router = APIRouter(prefix="/doc",tags=["Document"])

@router.post("/",response_model=StandardResponse[List[DocOutput]] , summary="Upload pdf file")
async def upload_file_ep(
    file: List[UploadFile] = File(...),
    organization_id: str = Query(...),
    db: AsyncDatabase = Depends(get_database)
):
    try:
        result = await upload_files(file, organization_id, db)
        # return result
        return StandardResponse(
            status="success",
            message=f"Successfully uploaded {len(result)} document(s)",
            data=result
        )
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

@router.get("/{organization_id}",response_model=StandardResponse[List[DocOutput]], summary="Get documents by organization ID")
async def get_docs_by_org_id(
    organization_id: str,
    db: AsyncDatabase = Depends(get_database)
):
    try:
        docs = await getDocsByOrgId(organization_id, db)
        # return docs
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(docs)} document(s) for organization {organization_id}",
            data=docs
        )
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )