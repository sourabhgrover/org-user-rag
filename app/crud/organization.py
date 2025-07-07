from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime
from bson import ObjectId
from typing import Optional,List,Dict,Any

from app.api.v1.models import OrganizationCreate , OrganizationInDB ,OrganizationUpdate

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


async def update_organization(
    db: AsyncDatabase,
    org_id: str,
    org_update: OrganizationUpdate
) -> Optional[OrganizationInDB]:
    """
    Updates an existing organization.
    Includes a uniqueness check if 'organization_name' is being updated.
    Returns None if org not found or if new name is not unique.
    """
    if not ObjectId.is_valid(org_id):
        return None

    update_data = org_update.model_dump(by_alias=True, exclude_unset=True)
    if not update_data: # No fields to update
        return await get_organization_by_id(db, org_id)

    # If organization_name is being updated, check for uniqueness (excluding current org)
    if "name" in update_data:
        existing_org = await get_organization_by_name(db, update_data["name"])
        if existing_org and str(existing_org.id) != org_id:
            return None # New name conflicts with another existing organization

    update_data["updated_at"] = datetime.utcnow()

    result = await db.organizations.update_one(
        {"_id": ObjectId(org_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None # Organization not found
    
    return await get_organization_by_id(db, org_id)

async def get_organizations(
    db: AsyncDatabase,
    skip: int = 0,
    limit: int = 100,
    search_name: Optional[str] = None
) -> List[OrganizationInDB]:
    """
    Retrieves a list of organizations with optional filtering and pagination.
    """
    query_filter: Dict[str, Any] = {}
    if search_name:
        query_filter["name"] = {"$regex": search_name, "$options": "i"}

    cursor = db.organizations.find(query_filter).skip(skip).limit(limit)
    organizations = await cursor.to_list(length=limit)
    return [OrganizationInDB(**org) for org in organizations]