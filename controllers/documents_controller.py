from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from pathlib import Path
import uuid
import logging

import cloudinary
import cloudinary.uploader

from database import db
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from controllers.settings_controller import get_cloudinary_config
from models.hrms import Employee

logger = logging.getLogger(__name__)


async def upload_document(
    file: UploadFile,
    project_id: str,
    category: str,
    description: str,
    current_user: Employee
) -> dict:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")

    doc_id = str(uuid.uuid4())
    original_name = file.filename
    content_type = file.content_type or "application/octet-stream"

    cloud_config = await get_cloudinary_config()
    if cloud_config:
        try:
            cloudinary.config(
                cloud_name=cloud_config["cloud_name"],
                api_key=cloud_config["api_key"],
                api_secret=cloud_config["api_secret"]
            )
            resource_type = "image" if ext in {'.png', '.jpg', '.jpeg', '.webp'} else "raw"
            upload_result = cloudinary.uploader.upload(
                content,
                public_id=f"civil_erp/{project_id}/{doc_id}",
                resource_type=resource_type,
                folder="civil_erp_docs"
            )
            file_url = upload_result.get("secure_url")
            storage_type = "cloudinary"
            cloudinary_public_id = upload_result.get("public_id")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}, falling back to local")
            local_path = UPLOAD_DIR / f"{doc_id}{ext}"
            local_path.write_bytes(content)
            file_url = f"/api/documents/file/{doc_id}{ext}"
            storage_type = "local"
            cloudinary_public_id = None
    else:
        local_path = UPLOAD_DIR / f"{doc_id}{ext}"
        local_path.write_bytes(content)
        file_url = f"/api/documents/file/{doc_id}{ext}"
        storage_type = "local"
        cloudinary_public_id = None

    doc = {
        "id": doc_id,
        "project_id": project_id,
        "filename": original_name,
        "file_url": file_url,
        "file_extension": ext,
        "content_type": content_type,
        "file_size": len(content),
        "storage_type": storage_type,
        "cloudinary_public_id": cloudinary_public_id,
        "category": category,
        "description": description,
        "uploaded_by": current_user.id,
        "uploaded_by_name": current_user.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.documents.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_documents(project_id=None) -> list:
    query = {"project_id": project_id} if project_id else {}
    return await db.documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)


async def get_document(doc_id: str) -> dict:
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def serve_local_file(filename: str) -> FileResponse:
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


async def delete_document(doc_id: str) -> dict:
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("storage_type") == "cloudinary" and doc.get("cloudinary_public_id"):
        cloud_config = await get_cloudinary_config()
        if cloud_config:
            try:
                cloudinary.config(
                    cloud_name=cloud_config["cloud_name"],
                    api_key=cloud_config["api_key"],
                    api_secret=cloud_config["api_secret"]
                )
                resource_type = "image" if doc.get("file_extension") in {'.png', '.jpg', '.jpeg', '.webp'} else "raw"
                cloudinary.uploader.destroy(doc["cloudinary_public_id"], resource_type=resource_type)
            except Exception as e:
                logger.error(f"Cloudinary delete failed: {e}")
    else:
        local_file = UPLOAD_DIR / f"{doc_id}{doc.get('file_extension', '')}"
        if local_file.exists():
            local_file.unlink()
    await db.documents.delete_one({"id": doc_id})
    return {"message": "Document deleted"}
