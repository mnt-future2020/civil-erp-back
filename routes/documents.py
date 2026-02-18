from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import documents_controller

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    category: str = Form("general"),
    description: str = Form(""),
    current_user: Employee = Depends(check_permission("projects", "create"))
):
    return await documents_controller.upload_document(file, project_id, category, description, current_user)


@router.get("")
async def list_documents(project_id: Optional[str] = None, exclude_category: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await documents_controller.list_documents(project_id, exclude_category)


@router.get("/{doc_id}/content")
async def serve_document_content(doc_id: str, current_user: Employee = Depends(get_current_user)):
    return await documents_controller.serve_document_content(doc_id)


@router.get("/{doc_id}")
async def get_document(doc_id: str, current_user: Employee = Depends(get_current_user)):
    return await documents_controller.get_document(doc_id)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, current_user: Employee = Depends(check_permission("projects", "delete"))):
    return await documents_controller.delete_document(doc_id)
