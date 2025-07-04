from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import Annotated, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class OrganizationBase(BaseModel):
    name: Annotated[str, Field(description="The name of the organization", min_length=1, max_length=100)]

class OrganizationCreate(OrganizationBase):
    """Model for creating a new organization."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

class OrganizationInDB(OrganizationBase):
    """Model for organizations as stored in the database, including MongoDB _id and timestamps."""
    id: PyObjectId = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )