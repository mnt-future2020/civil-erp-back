from typing import Optional
from fastapi import HTTPException
from database import db
from models.contractor import Contractor, ContractorCreate, ContractorUpdate
from models.hrms import Employee


async def list_contractors(project_id: Optional[str] = None):
    query = {"project_id": project_id} if project_id else {}
    return await db.contractors.find(query, {"_id": 0}).to_list(1000)


async def create_contractor(data: ContractorCreate, current_user: Employee) -> dict:
    existing = await db.contractors.find_one({"contractor_code": data.contractor_code})
    if existing:
        raise HTTPException(status_code=400, detail="Contractor code already exists")
    doc = Contractor(**data.model_dump(), created_by=current_user.id)
    await db.contractors.insert_one(doc.model_dump())
    return await db.contractors.find_one({"id": doc.id}, {"_id": 0})


async def update_contractor(contractor_id: str, data: ContractorUpdate) -> dict:
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = await db.contractors.update_one({"id": contractor_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return await db.contractors.find_one({"id": contractor_id}, {"_id": 0})


async def delete_contractor(contractor_id: str):
    result = await db.contractors.delete_one({"id": contractor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return {"message": "Deleted"}
