from fastapi import APIRouter, Depends
from models.rbac import Role, RoleCreate, RoleUpdate
from models.auth import UserRoleAssign
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import rbac_controller

router = APIRouter(tags=["rbac"])


@router.get("/roles")
async def get_roles(current_user: Employee = Depends(get_current_user)):
    return await rbac_controller.get_roles()


@router.get("/roles/{role_id}")
async def get_role(role_id: str, current_user: Employee = Depends(get_current_user)):
    return await rbac_controller.get_role(role_id)


@router.post("/roles", response_model=Role)
async def create_role(role_data: RoleCreate, current_user: Employee = Depends(check_permission("hrms", "create"))):
    return await rbac_controller.create_role(role_data)


@router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: RoleUpdate, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    return await rbac_controller.update_role(role_id, role_data)


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    return await rbac_controller.delete_role(role_id)


@router.get("/users")
async def get_users(current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await rbac_controller.get_users()


@router.patch("/users/{user_id}/role")
async def assign_user_role(user_id: str, data: UserRoleAssign, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    return await rbac_controller.assign_user_role(user_id, data)
