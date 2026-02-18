from typing import Optional
from fastapi import APIRouter, Depends
from controllers import contractor_controller
from models.contractor import ContractorCreate, ContractorUpdate
from core.auth import get_current_user
from models.hrms import Employee

router = APIRouter(prefix="/contractors", tags=["contractors"])


@router.get("/")
async def list_contractors(project_id: Optional[str] = None):
    return await contractor_controller.list_contractors(project_id)


@router.post("/")
async def create_contractor(data: ContractorCreate, current_user: Employee = Depends(get_current_user)):
    return await contractor_controller.create_contractor(data, current_user)


@router.patch("/{contractor_id}")
async def update_contractor(contractor_id: str, data: ContractorUpdate, current_user: Employee = Depends(get_current_user)):
    return await contractor_controller.update_contractor(contractor_id, data)


@router.delete("/{contractor_id}")
async def delete_contractor(contractor_id: str, current_user: Employee = Depends(get_current_user)):
    return await contractor_controller.delete_contractor(contractor_id)
