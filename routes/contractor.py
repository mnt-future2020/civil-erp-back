from typing import Optional
from fastapi import APIRouter, Depends, Request
from controllers import contractor_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua
from models.contractor import ContractorCreate, ContractorUpdate
from core.auth import get_current_user, check_permission
from models.hrms import Employee

router = APIRouter(prefix="/contractors", tags=["contractors"])


@router.get("/")
async def list_contractors(project_id: Optional[str] = None, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await contractor_controller.list_contractors(project_id)


@router.post("/")
async def create_contractor(data: ContractorCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await contractor_controller.create_contractor(data, current_user)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "contractors", "contractor", f"Created contractor '{data.name}'", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.patch("/{contractor_id}")
async def update_contractor(contractor_id: str, data: ContractorUpdate, request: Request, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    result = await contractor_controller.update_contractor(contractor_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "contractors", "contractor", "Updated contractor", contractor_id, _ip(request), _ua(request))
    return result


@router.delete("/{contractor_id}")
async def delete_contractor(contractor_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await contractor_controller.delete_contractor(contractor_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "contractors", "contractor", "Deleted contractor", contractor_id, _ip(request), _ua(request))
    return result
