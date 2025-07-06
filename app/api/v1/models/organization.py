from pydantic import BaseModel,Field
from typing import Annotated
from datetime import datetime

class OrganizationBase(BaseModel):
    name: Annotated[str, Field(description="The name of the organization", min_length=1,max_length=100)]

class OrganizationCreate(OrganizationBase):
    """Model for creating a new organization."""
    pass

class OrganizationInDB(OrganizationBase):
    """Model for organizations as stored in the database, including MongoDB _id and timestamps."""
    # created_at: Annotated[str, Field(default_factory=lambda: datetime.utcnow().isoformat())]
    # updated_at: Annotated[str, Field(default_factory=lambda: datetime.utcnow().isoformat())]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # class Config:
    #     """Configuration for Pydantic models."""
    #     allow_population_by_field_name = True
    #     json_encoders = {
    #         str: lambda v: str(v)
    #     }