from pymongo.asynchronous.database import AsyncDatabase
from app.api.v1.models import OrganizationCreate , OrganizationInDB
from datetime import datetime

async def create_organization(db: AsyncDatabase, create_organization: OrganizationCreate):
    create_organization_data = create_organization.model_dump()
    # Add timestamps
    create_organization_data['created_at'] = datetime.utcnow()
    create_organization_data['updated_at'] = datetime.utcnow()
    
    result = await db.organizations.insert_one(create_organization_data)
    new_organization = await db.organizations.find_one({"_id": result.inserted_id})
    return OrganizationInDB(**new_organization)