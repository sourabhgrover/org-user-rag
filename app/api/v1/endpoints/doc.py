from fastapi import APIRouter,Depends,UploadFile,File,Query,HTTPException
from typing import List
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.crud.doc import upload_files

router = APIRouter(prefix="/doc")

@router.post("/",summary="Upload pdf file")
async def upload_file_ep(file:List[UploadFile] = File(...),organization_id:str = Query(...),db:AsyncDatabase = Depends(get_database)):
        try:
            result = await upload_files(file,organization_id,db)
            return result
        except Exception as e:
              raise HTTPException(f"Exceptioon {e}")
    # return {}