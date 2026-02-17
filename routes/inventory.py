from fastapi import APIRouter, Depends
from typing import Optional
from models.inventory import InventoryItem, InventoryItemCreate, InventoryItemUpdate, InventoryQuantityUpdate, InventoryTransfer
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import inventory_controller

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/dashboard")
async def get_dashboard(project_id: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await inventory_controller.get_dashboard(project_id)


@router.post("", response_model=InventoryItem)
async def create_item(data: InventoryItemCreate, current_user: Employee = Depends(check_permission("inventory", "create"))):
    return await inventory_controller.create_item(data, current_user)


@router.get("")
async def get_items(project_id: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await inventory_controller.get_items(project_id, category, status)


@router.get("/{item_id}")
async def get_item(item_id: str, current_user: Employee = Depends(get_current_user)):
    return await inventory_controller.get_item(item_id)


@router.put("/{item_id}")
async def update_item(item_id: str, data: InventoryItemUpdate, current_user: Employee = Depends(check_permission("inventory", "edit"))):
    return await inventory_controller.update_item(item_id, data)


@router.patch("/{item_id}/quantity")
async def update_quantity(item_id: str, data: InventoryQuantityUpdate, current_user: Employee = Depends(check_permission("inventory", "edit"))):
    return await inventory_controller.update_quantity(item_id, data)


@router.post("/transfer")
async def transfer_material(data: InventoryTransfer, current_user: Employee = Depends(check_permission("inventory", "edit"))):
    return await inventory_controller.transfer_material(data, current_user)


@router.delete("/{item_id}")
async def delete_item(item_id: str, current_user: Employee = Depends(check_permission("inventory", "delete"))):
    return await inventory_controller.delete_item(item_id)
