from fastapi import APIRouter, Depends, UploadFile, File, Request
from models.auth import UserLogin, Token, User, ProfileUpdate, PasswordChange
from models.hrms import Employee
from core.auth import get_current_user
from controllers import auth_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request):
    result = await auth_controller.login(credentials)
    await log_audit(result.user.id, result.user.name, result.user.role, "LOGIN", "auth", "session", "Logged in", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.get("/me", response_model=User)
async def get_me(current_user: Employee = Depends(get_current_user)):
    return await auth_controller.get_me(current_user)


@router.patch("/profile", response_model=User)
async def update_profile(data: ProfileUpdate, request: Request, current_user: Employee = Depends(get_current_user)):
    result = await auth_controller.update_profile(current_user, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "auth", "profile", "Updated profile", current_user.id, _ip(request), _ua(request))
    return result


@router.post("/change-password")
async def change_password(data: PasswordChange, request: Request, current_user: Employee = Depends(get_current_user)):
    result = await auth_controller.change_password(current_user, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "auth", "password", "Changed password", current_user.id, _ip(request), _ua(request))
    return result


@router.post("/avatar", response_model=User)
async def update_avatar(file: UploadFile = File(...), current_user: Employee = Depends(get_current_user)):
    file_bytes = await file.read()
    return await auth_controller.update_avatar(current_user, file_bytes, file.content_type)


@router.get("/permissions")
async def get_my_permissions(current_user: Employee = Depends(get_current_user)):
    return await auth_controller.get_my_permissions(current_user)
