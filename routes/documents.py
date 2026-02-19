from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from typing import Optional
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import documents_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    project_id: str = Form(...),
    category: str = Form("general"),
    description: str = Form(""),
    current_user: Employee = Depends(check_permission("projects", "create"))
):
    result = await documents_controller.upload_document(file, project_id, category, description, current_user)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "documents", "document", f"Uploaded '{file.filename}'", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.get("")
async def list_documents(project_id: Optional[str] = None, exclude_category: Optional[str] = None, current_user: Employee = Depends(check_permission("projects", "view"))):
    return await documents_controller.list_documents(project_id, exclude_category)


@router.get("/{doc_id}/content")
async def serve_document_content(doc_id: str, current_user: Employee = Depends(check_permission("projects", "view"))):
    return await documents_controller.serve_document_content(doc_id)


@router.get("/{doc_id}")
async def get_document(doc_id: str, current_user: Employee = Depends(check_permission("projects", "view"))):
    return await documents_controller.get_document(doc_id)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, request: Request, current_user: Employee = Depends(check_permission("projects", "delete"))):
    result = await documents_controller.delete_document(doc_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "documents", "document", "Deleted document", doc_id, _ip(request), _ua(request))
    return result
