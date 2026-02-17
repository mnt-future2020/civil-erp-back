from fastapi import APIRouter, Depends, UploadFile, File
from models.auth import UserLogin, Token, User, ProfileUpdate, PasswordChange
from models.hrms import Employee
from core.auth import get_current_user
from controllers import auth_controller

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    return await auth_controller.login(credentials)


@router.get("/me", response_model=User)
async def get_me(current_user: Employee = Depends(get_current_user)):
    return await auth_controller.get_me(current_user)


@router.patch("/profile", response_model=User)
async def update_profile(data: ProfileUpdate, current_user: Employee = Depends(get_current_user)):
    return await auth_controller.update_profile(current_user, data)


@router.post("/change-password")
async def change_password(data: PasswordChange, current_user: Employee = Depends(get_current_user)):
    return await auth_controller.change_password(current_user, data)


@router.post("/avatar", response_model=User)
async def update_avatar(file: UploadFile = File(...), current_user: Employee = Depends(get_current_user)):
    file_bytes = await file.read()
    return await auth_controller.update_avatar(current_user, file_bytes, file.content_type)


@router.get("/permissions")
async def get_my_permissions(current_user: Employee = Depends(get_current_user)):
    return await auth_controller.get_my_permissions(current_user)
