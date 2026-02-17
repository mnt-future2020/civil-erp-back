from fastapi import HTTPException
from datetime import datetime, timezone

from database import db
from models.rbac import Role, RoleCreate, RoleUpdate
from models.auth import UserRoleAssign
from config import MODULES


async def get_roles() -> list:
    return await db.roles.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)


async def get_role(role_id: str) -> dict:
    role = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


async def create_role(role_data: RoleCreate) -> Role:
    existing = await db.roles.find_one({"name": role_data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")
    for module in role_data.permissions:
        if module not in MODULES:
            raise HTTPException(status_code=400, detail=f"Invalid module: {module}")
    full_permissions = {}
    for module in MODULES:
        if module in role_data.permissions:
            full_permissions[module] = role_data.permissions[module].model_dump()
        else:
            full_permissions[module] = {"view": False, "create": False, "edit": False, "delete": False}
    role = Role(
        name=role_data.name,
        label=role_data.label,
        description=role_data.description,
        permissions=full_permissions,
    )
    await db.roles.insert_one(role.model_dump())
    return role


async def update_role(role_id: str, role_data: RoleUpdate) -> dict:
    existing = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    if existing.get("name") == "admin":
        raise HTTPException(status_code=400, detail="Cannot modify admin role")
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if role_data.label is not None:
        update["label"] = role_data.label
    if role_data.description is not None:
        update["description"] = role_data.description
    if role_data.permissions is not None:
        for module in role_data.permissions:
            if module not in MODULES:
                raise HTTPException(status_code=400, detail=f"Invalid module: {module}")
        merged = existing.get("permissions", {})
        for module, perms in role_data.permissions.items():
            merged[module] = perms.model_dump()
        update["permissions"] = merged
    await db.roles.update_one({"id": role_id}, {"$set": update})
    return await db.roles.find_one({"id": role_id}, {"_id": 0})


async def delete_role(role_id: str) -> dict:
    existing = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    if existing.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    employees_with_role = await db.employees.count_documents({"role": existing["name"]})
    if employees_with_role > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete role: {employees_with_role} employee(s) still assigned")
    await db.roles.delete_one({"id": role_id})
    return {"message": "Role deleted"}


async def get_users() -> list:
    return await db.employees.find({}, {"_id": 0, "password": 0}).to_list(1000)


async def assign_user_role(user_id: str, data: UserRoleAssign) -> dict:
    employee = await db.employees.find_one({"id": user_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    role = await db.roles.find_one({"name": data.role})
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{data.role}' does not exist")
    await db.employees.update_one({"id": user_id}, {"$set": {"role": data.role}})
    return {"message": f"Role updated to '{data.role}'"}
