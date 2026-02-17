from fastapi import APIRouter, Depends
from typing import Optional
from models.einvoice import EInvoiceCreate
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import einvoice_controller

router = APIRouter(tags=["einvoice"])


@router.post("/einvoice/generate")
async def generate_einvoice(invoice_data: EInvoiceCreate, current_user: Employee = Depends(check_permission("einvoicing", "create"))):
    return await einvoice_controller.generate_einvoice(invoice_data)


@router.get("/einvoice")
async def list_einvoices(status: Optional[str] = None, current_user: Employee = Depends(check_permission("einvoicing", "view"))):
    return await einvoice_controller.list_einvoices(status)


@router.get("/einvoice/{einvoice_id}")
async def get_einvoice(einvoice_id: str, current_user: Employee = Depends(check_permission("einvoicing", "view"))):
    return await einvoice_controller.get_einvoice(einvoice_id)


@router.post("/einvoice/{einvoice_id}/cancel")
async def cancel_einvoice(einvoice_id: str, reason: str = "Data entry error", current_user: Employee = Depends(check_permission("einvoicing", "edit"))):
    return await einvoice_controller.cancel_einvoice(einvoice_id, reason)


@router.get("/einvoice-stats")
async def get_einvoice_stats(current_user: Employee = Depends(check_permission("einvoicing", "view"))):
    return await einvoice_controller.get_einvoice_stats()
