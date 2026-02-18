from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
from datetime import datetime, timezone
from pathlib import Path
import uuid
import logging

import httpx
import cloudinary
import cloudinary.uploader

from database import db
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from controllers.settings_controller import get_cloudinary_config
from models.hrms import Employee

logger = logging.getLogger(__name__)


async def _configure_cloudinary():
    """Load Cloudinary config from settings and apply it. Raises if not configured."""
    cloud_config = await get_cloudinary_config()
    if not cloud_config:
        raise HTTPException(status_code=400, detail="Cloudinary is not configured. Go to Settings → Cloudinary to set it up.")
    cloudinary.config(
        cloud_name=cloud_config["cloud_name"],
        api_key=cloud_config["api_key"],
        api_secret=cloud_config["api_secret"]
    )
    return cloud_config


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

    # Upload to Cloudinary
    try:
        await _configure_cloudinary()
        resource_type = "image" if ext in {'.png', '.jpg', '.jpeg', '.webp'} else "raw"
        upload_result = cloudinary.uploader.upload(
            content,
            public_id=f"civil_erp/{project_id}/{doc_id}",
            resource_type=resource_type,
            folder="civil_erp_docs"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(status_code=502, detail=f"Cloud upload failed: {e}")

    doc = {
        "id": doc_id,
        "project_id": project_id,
        "filename": original_name,
        "file_url": upload_result.get("secure_url"),
        "file_extension": ext,
        "content_type": content_type,
        "file_size": len(content),
        "storage_type": "cloudinary",
        "cloudinary_public_id": upload_result.get("public_id"),
        "category": category,
        "description": description,
        "uploaded_by": current_user.id,
        "uploaded_by_name": current_user.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.documents.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_documents(project_id=None, exclude_category=None) -> list:
    query = {}
    if project_id:
        query["project_id"] = project_id
    if exclude_category:
        query["category"] = {"$ne": exclude_category}
    return await db.documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)


async def get_document(doc_id: str) -> dict:
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


async def serve_document_content(doc_id: str):
    """Proxy endpoint — fetches file bytes from Cloudinary and serves them."""
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_url = doc.get("file_url")
    if not file_url:
        raise HTTPException(status_code=404, detail="No file URL for this document")

    content_type = doc.get("content_type", "application/octet-stream")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(file_url)
            resp.raise_for_status()
        return Response(content=resp.content, media_type=content_type)
    except Exception as e:
        logger.error(f"Failed to proxy file {doc_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch file from cloud storage")


async def delete_document(doc_id: str) -> dict:
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("cloudinary_public_id"):
        try:
            await _configure_cloudinary()
            resource_type = "image" if doc.get("file_extension") in {'.png', '.jpg', '.jpeg', '.webp'} else "raw"
            cloudinary.uploader.destroy(doc["cloudinary_public_id"], resource_type=resource_type)
        except Exception as e:
            logger.error(f"Cloudinary delete failed: {e}")
    await db.documents.delete_one({"id": doc_id})
    return {"message": "Document deleted"}
