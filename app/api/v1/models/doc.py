from pydantic import BaseModel,Field
from datetime import datetime
from typing import Annotated

class DocBase(BaseModel):
    organization_id: Annotated[str,Field()]
    ame:Annotated[str, Field(max_length=200,description="Name of the file")]


class DocOutput(DocBase):
    id:Annotated[str,Field(alias="_id", description="Unique id of the Document")] 
    unique_filename:str
    path:str
    uploadedAt:datetime
    class Config:
        populate_by_name = True