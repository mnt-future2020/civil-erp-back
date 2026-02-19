from fastapi import APIRouter, Depends, Request
from models.rbac import Role, RoleCreate, RoleUpdate
from models.auth import UserRoleAssign
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import rbac_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(tags=["rbac"])


@router.get("/roles")
async def get_roles(current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await rbac_controller.get_roles()


@router.get("/roles/{role_id}")
async def get_role(role_id: str, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await rbac_controller.get_role(role_id)


@router.post("/roles", response_model=Role)
async def create_role(role_data: RoleCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await rbac_controller.create_role(role_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "rbac", "role", f"Created role '{role_data.name}'", result.id, _ip(request), _ua(request))
    return result


@router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: RoleUpdate, request: Request, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    result = await rbac_controller.update_role(role_id, role_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "rbac", "role", f"Updated role permissions", role_id, _ip(request), _ua(request))
    return result


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await rbac_controller.delete_role(role_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "rbac", "role", "Deleted role", role_id, _ip(request), _ua(request))
    return result


@router.get("/users")
async def get_users(current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await rbac_controller.get_users()


@router.patch("/users/{user_id}/role")
async def assign_user_role(user_id: str, data: UserRoleAssign, request: Request, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    result = await rbac_controller.assign_user_role(user_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "rbac", "user_role", f"Assigned role '{data.role}' to user", user_id, _ip(request), _ua(request))
    return result
