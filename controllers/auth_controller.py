from fastapi import HTTPException
import base64
from database import db
from models.auth import UserLogin, Token, User, ProfileUpdate, PasswordChange
from models.hrms import Employee
from core.auth import verify_password, get_password_hash, create_access_token
from config import MODULES


async def login(credentials: UserLogin) -> Token:
    emp_doc = await db.employees.find_one({"email": credentials.email})
    if not emp_doc or not verify_password(credentials.password, emp_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    emp_obj = Employee(**{k: v for k, v in emp_doc.items() if k not in ['_id', 'password']})
    access_token = create_access_token({"sub": emp_obj.id, "role": emp_obj.role})

    return Token(access_token=access_token, user=User(
        id=emp_obj.id,
        email=emp_obj.email,
        name=emp_obj.name,
        role=emp_obj.role,
        phone=emp_obj.phone,
        department=emp_obj.department,
        avatar_url=emp_obj.avatar_url,
        created_at=emp_obj.created_at,
        is_active=emp_obj.is_active
    ))


async def get_me(current_user: Employee) -> User:
    return User(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        phone=current_user.phone,
        department=current_user.department,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


async def update_profile(current_user: Employee, data: ProfileUpdate) -> User:
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "email" in updates:
        existing = await db.employees.find_one({"email": updates["email"], "id": {"$ne": current_user.id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    await db.employees.update_one({"id": current_user.id}, {"$set": updates})
    updated = await db.employees.find_one({"id": current_user.id}, {"_id": 0, "password": 0})
    return User(**updated)


async def change_password(current_user: Employee, data: PasswordChange) -> dict:
    emp_doc = await db.employees.find_one({"id": current_user.id})
    if not verify_password(data.current_password, emp_doc["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    hashed = get_password_hash(data.new_password)
    await db.employees.update_one({"id": current_user.id}, {"$set": {"password": hashed}})
    return {"message": "Password updated successfully"}


async def update_avatar(current_user: Employee, file_bytes: bytes, content_type: str) -> User:
    # Store as base64 data URL (works without Cloudinary for small profile photos)
    b64 = base64.b64encode(file_bytes).decode()
    avatar_url = f"data:{content_type};base64,{b64}"
    await db.employees.update_one({"id": current_user.id}, {"$set": {"avatar_url": avatar_url}})
    updated = await db.employees.find_one({"id": current_user.id}, {"_id": 0, "password": 0})
    return User(**updated)


async def get_my_permissions(current_user: Employee) -> dict:
    if current_user.role == "admin":
        perms = {module: {"view": True, "create": True, "edit": True, "delete": True} for module in MODULES}
        return {"role": "admin", "permissions": perms}
    role_doc = await db.roles.find_one({"name": current_user.role}, {"_id": 0})
    if not role_doc:
        perms = {module: {"view": False, "create": False, "edit": False, "delete": False} for module in MODULES}
        return {"role": current_user.role, "permissions": perms}
    return {"role": current_user.role, "permissions": role_doc.get("permissions", {})}
