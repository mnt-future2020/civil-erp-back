from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from models.settings import GSTCredentialsCreate, CloudinaryCredentials, SMTPCredentials
from models.hrms import Employee
from core.auth import check_permission
from controllers import settings_controller


class SendTestEmailRequest(BaseModel):
    to_email: EmailStr

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/gst-credentials")
async def save_gst_credentials(creds: GSTCredentialsCreate, current_user: Employee = Depends(check_permission("settings", "edit"))):
    return await settings_controller.save_gst_credentials(creds, current_user.id)


@router.get("/gst-credentials")
async def get_gst_credentials(current_user: Employee = Depends(check_permission("settings", "view"))):
    return await settings_controller.get_gst_credentials()


@router.delete("/gst-credentials")
async def delete_gst_credentials(current_user: Employee = Depends(check_permission("settings", "delete"))):
    return await settings_controller.delete_gst_credentials()


@router.post("/gst-credentials/test")
async def test_gst_connection(current_user: Employee = Depends(check_permission("settings", "edit"))):
    return await settings_controller.test_gst_connection()


@router.post("/cloudinary")
async def save_cloudinary_credentials(creds: CloudinaryCredentials, current_user: Employee = Depends(check_permission("settings", "edit"))):
    return await settings_controller.save_cloudinary_credentials(creds, current_user.id)


@router.get("/cloudinary")
async def get_cloudinary_credentials(current_user: Employee = Depends(check_permission("settings", "view"))):
    return await settings_controller.get_cloudinary_credentials()


@router.delete("/cloudinary")
async def delete_cloudinary_credentials(current_user: Employee = Depends(check_permission("settings", "delete"))):
    return await settings_controller.delete_cloudinary_credentials()


# ── SMTP ──────────────────────────────────────────────────

@router.post("/smtp")
async def save_smtp_credentials(creds: SMTPCredentials, current_user: Employee = Depends(check_permission("settings", "edit"))):
    return await settings_controller.save_smtp_credentials(creds, current_user.id)


@router.get("/smtp")
async def get_smtp_credentials(current_user: Employee = Depends(check_permission("settings", "view"))):
    return await settings_controller.get_smtp_credentials()


@router.delete("/smtp")
async def delete_smtp_credentials(current_user: Employee = Depends(check_permission("settings", "delete"))):
    return await settings_controller.delete_smtp_credentials()


@router.post("/smtp/test")
async def test_smtp_connection(current_user: Employee = Depends(check_permission("settings", "edit"))):
    return await settings_controller.test_smtp_connection()


@router.post("/smtp/send-test")
async def send_test_email(body: SendTestEmailRequest, current_user: Employee = Depends(check_permission("settings", "edit"))):
    return await settings_controller.send_test_email(body.to_email)
