from fastapi import APIRouter,Depends,UploadFile,File,Query,HTTPException,status
from typing import List
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.crud.doc import upload_files, getDocsByOrgId
from app.api.v1.models.doc import DocOutput
from app.api.v1.models.response import StandardResponse
from app.core.dependencies import get_current_active_user
from app.api.v1.models.user import UserInDB

router = APIRouter(prefix="/doc",tags=["Doc"],dependencies=[Depends(get_current_active_user)])

@router.post("/",response_model=StandardResponse[List[DocOutput]] , summary="Upload pdf file")
async def upload_file_ep(
    file: List[UploadFile] = File(...),
    # organization_id: str = Query(...),
    db: AsyncDatabase = Depends(get_database),
    current_user : UserInDB = Depends(get_current_active_user)
):
    try:
        result = await upload_files(file, current_user.organization_id, db)
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

@router.get("/",response_model=StandardResponse[List[DocOutput]], summary="Get all documents")
async def get_docs_by_org_id(
    db: AsyncDatabase = Depends(get_database),
    current_user : UserInDB = Depends(get_current_active_user)
):
    try:
        docs = await getDocsByOrgId(current_user.organization_id, db)
        # return docs
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(docs)} document(s) for organization {current_user.organization_id}",
            data=docs
        )
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )