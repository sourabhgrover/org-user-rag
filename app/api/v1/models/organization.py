from pydantic import BaseModel,Field,BeforeValidator
from typing import Annotated
from datetime import datetime
from bson import ObjectId # For MongoDB's native ObjectId

# Custom type for ObjectId handling in Pydantic
# This allows Pydantic to validate string IDs and convert them to ObjectId for MongoDB
PyObjectId = Annotated[str, BeforeValidator(str)]

class OrganizationBase(BaseModel):
    name: Annotated[str, Field(description="The name of the organization", min_length=1,max_length=100)]

class OrganizationCreate(OrganizationBase):
    """Model for creating a new organization."""
    pass

class OrganizationUpdate(OrganizationBase):
    name : Annotated[str, Field(description="The name of the organization", min_length=1,max_length=100)] = None

class OrganizationInDB(OrganizationBase):
    """Model for organizations as stored in the database, including MongoDB _id and timestamps."""
     # Properties:
    id: PyObjectId = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    # """
    # - **`id`**: This is the unique identifier for the user.
    # - **`PyObjectId`**: A custom Pydantic type annotation that tells Pydantic:
    #     - This field should be treated as a string (`str`) for Python type checking.
    #     - But `BeforeValidator(str)` ensures that if a `bson.ObjectId` object is passed (which is what PyMongo returns), it gets converted to a string before Pydantic validates it. This is crucial for handling MongoDB's native ID type.
    # - **`Field(alias="_id", ...)`**:
    #     - **`alias="_id"`**: This is very important! MongoDB's primary key field is always named `_id`. In Python, attribute names usually don't start with an underscore (`_`) unless they're "private." The `alias` setting tells Pydantic: "When I'm working with this model in Python, I'll refer to this field as `id`. But when Pydantic interacts with the underlying data (like a MongoDB document), map it to the `_id` field."
    #     - **`default_factory=lambda: str(ObjectId())`**: This provides a way for Pydantic to *generate* a default `ObjectId` (and convert it to a string) if you were to create an instance of `UserInDB` without explicitly providing an `id`. While we generally let MongoDB generate the `_id` on insertion, this `default_factory` is useful when you might be constructing `UserInDB` objects from partial data or for testing purposes.
    # """
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

class OrganizationResponse(OrganizationInDB):
    pass