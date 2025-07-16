from pydantic import BaseModel,Field
from datetime import datetime
from typing import Annotated
from bson import ObjectId


class DocBase(BaseModel):
    organization_id: Annotated[str,Field()]
    name: Annotated[str, Field(max_length=200,description="Name of the file")]


class DocOutput(DocBase):
    id: Annotated[str, Field(description="Unique id of the Document")] 
    unique_filename: str
    path: str
    uploadedAt: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}