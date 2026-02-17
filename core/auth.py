from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from typing import List
import jwt

from config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS, MODULES
from database import db

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        emp_doc = await db.employees.find_one({"id": user_id}, {"_id": 0})
        if emp_doc is None:
            raise HTTPException(status_code=401, detail="Employee not found")
        from models.hrms import Employee
        return Employee(**emp_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def check_role(allowed_roles: List[str]):
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker


def check_permission(module: str, action: str):
    async def permission_checker(current_user=Depends(get_current_user)):
        if current_user.role == "admin":
            return current_user
        role_doc = await db.roles.find_one({"name": current_user.role}, {"_id": 0})
        if not role_doc:
            raise HTTPException(status_code=403, detail="Role not found. Contact admin.")
        permissions = role_doc.get("permissions", {})
        module_perms = permissions.get(module, {})
        if not module_perms.get(action, False):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return permission_checker
