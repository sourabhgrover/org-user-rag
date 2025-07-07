from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.api.v1.models import OrganizationCreate , OrganizationInDB

async def delete_organization_by_id(db: AsyncDatabase, org_id: str) -> bool:
      # Perform the deletion
        result = await db.organizations.delete_one({"_id": ObjectId(org_id)})
        return result.deleted_count > 0

async def get_organization_by_name(db: AsyncDatabase, name: str):
    
    org_doc =  await db.organizations.find_one({"name": name})
    if org_doc:
        return OrganizationInDB(**org_doc)
    return None

async def get_organization_by_id(db: AsyncDatabase, org_id: str) -> Optional[OrganizationInDB]:
    org_doc = await db.organizations.find_one({"_id": ObjectId(org_id)})
    if org_doc:
        return OrganizationInDB(**org_doc)
    return None

async def create_organization(db: AsyncDatabase, create_organization: OrganizationCreate):

    #1 Check if organization already exists
    existing_org = await get_organization_by_name(db, create_organization.name)
    if existing_org:
        return None
    create_organization_data = create_organization.model_dump()
    # Add timestamps as datetime objects
    create_organization_data['created_at'] = datetime.utcnow()
    create_organization_data['updated_at'] = datetime.utcnow()
    
    result = await db.organizations.insert_one(create_organization_data)
    new_organization = await db.organizations.find_one({"_id": result.inserted_id})
    return OrganizationInDB(**new_organization)