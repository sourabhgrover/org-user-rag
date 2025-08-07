import os
from fastapi import  UploadFile,HTTPException,status
from app.api.v1.models.doc  import  DocOutput
from pymongo.asynchronous.database import AsyncDatabase
# from core import BadRequestException,  logger
from datetime import datetime
from typing import List
from bson import ObjectId

from app.services import rag_service , document_service



async def upload_files(
    files: List[UploadFile],
    organizationId: str,
    db: AsyncDatabase 
) -> List[DocOutput]:
    try:
        UPLOAD_DIR = "uploaded_files"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        documents_to_insert = []

        for file in files:
            # Validate file type
            if file.content_type != "application/pdf":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="File type not supported")

            # Generate unique filename
            timestamp = datetime.utcnow().isoformat().replace(":", "-")
            unique_filename = f"{organizationId}_{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)

            # Save the file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            doc = {
                "organizationId": organizationId,  # Store as string, not ObjectId
                "name": file.filename,
                "unique_filename": unique_filename,
                "path": file_path,
                "uploadedAt": datetime.utcnow(),
                "processed_for_rag": False
            }

            documents_to_insert.append(doc)

        # Insert into DB
        uploaded_docs = []
        if documents_to_insert:
            insert_result = await db.documents.insert_many(documents_to_insert)
            if not insert_result.acknowledged:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Failed to insert documents into database")
            
            # Convert inserted documents to DocOutput format
            for i, doc in enumerate(documents_to_insert):
                document_id = str(insert_result.inserted_ids[i])
                doc_output = DocOutput(
                    id=document_id,
                    organization_id=doc["organizationId"],
                    name=doc["name"],
                    unique_filename=doc["unique_filename"],
                    path=doc["path"],
                    uploadedAt=doc["uploadedAt"]
                )
                uploaded_docs.append(doc_output)

                # HERE WE WILL START MAGIC
                document_service.process_documents(doc["path"],document_id);        

        return uploaded_docs

    except Exception as e:
        # raise BadRequestException(f"Error in uploading files: {str(e)}")
        raise Exception(f"Error in uploading files: {str(e)}")

async def getDocsByOrgId(orgId: str, db) -> List[DocOutput]:
    try:
        docs_cursor = db.documents.find({"organizationId": orgId})
        docs = []
        async for doc in docs_cursor:
            # Convert ObjectId to string and map fields properly
            doc_data = {
                "id": str(doc["_id"]),
                "organization_id": doc["organizationId"],  # Map to organization_id
                "name": doc["name"],
                "unique_filename": doc["unique_filename"],
                "path": doc["path"],
                "uploadedAt": doc["uploadedAt"]
            }
            docs.append(DocOutput(**doc_data))
        return docs

    except Exception as e:
        # logger.exception("Failed to fetch Documents by OrganizationId")
        # raise DatabaseQueryException(f"Failed to get Documents details {e}")
        raise Exception(f"Failed to get Documents details {e}")