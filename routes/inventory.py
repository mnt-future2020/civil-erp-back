from fastapi import APIRouter, Depends, Request
from typing import Optional
from models.inventory import InventoryItem, InventoryItemCreate, InventoryItemUpdate, InventoryQuantityUpdate, InventoryTransfer
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import inventory_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/dashboard")
async def get_dashboard(project_id: Optional[str] = None, current_user: Employee = Depends(check_permission("inventory", "view"))):
    return await inventory_controller.get_dashboard(project_id)


@router.post("", response_model=InventoryItem)
async def create_item(data: InventoryItemCreate, request: Request, current_user: Employee = Depends(check_permission("inventory", "create"))):
    result = await inventory_controller.create_item(data, current_user)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "inventory", "item", f"Created inventory item '{data.name}'", result.id, _ip(request), _ua(request))
    return result


@router.get("")
async def get_items(project_id: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None, current_user: Employee = Depends(check_permission("inventory", "view"))):
    return await inventory_controller.get_items(project_id, category, status)


@router.get("/{item_id}")
async def get_item(item_id: str, current_user: Employee = Depends(check_permission("inventory", "view"))):
    return await inventory_controller.get_item(item_id)


@router.put("/{item_id}")
async def update_item(item_id: str, data: InventoryItemUpdate, request: Request, current_user: Employee = Depends(check_permission("inventory", "edit"))):
    result = await inventory_controller.update_item(item_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "inventory", "item", f"Updated inventory item", item_id, _ip(request), _ua(request))
    return result


@router.patch("/{item_id}/quantity")
async def update_quantity(item_id: str, data: InventoryQuantityUpdate, request: Request, current_user: Employee = Depends(check_permission("inventory", "edit"))):
    result = await inventory_controller.update_quantity(item_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "inventory", "item", f"Updated quantity", item_id, _ip(request), _ua(request))
    return result


@router.post("/transfer")
async def transfer_material(data: InventoryTransfer, request: Request, current_user: Employee = Depends(check_permission("inventory", "edit"))):
    result = await inventory_controller.transfer_material(data, current_user)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "inventory", "transfer", f"Transferred material — qty: {data.quantity}", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.delete("/{item_id}")
async def delete_item(item_id: str, request: Request, current_user: Employee = Depends(check_permission("inventory", "delete"))):
    result = await inventory_controller.delete_item(item_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "inventory", "item", "Deleted inventory item", item_id, _ip(request), _ua(request))
    return result
