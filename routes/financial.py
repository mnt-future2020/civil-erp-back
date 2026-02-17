from fastapi import APIRouter, Depends
from typing import List, Optional
from models.financial import CVR, CVRCreate, Billing, BillingCreate, BillingStatusUpdate
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import financial_controller

router = APIRouter(tags=["financial"])


@router.post("/cvr", response_model=CVR)
async def create_cvr(cvr_data: CVRCreate, current_user: Employee = Depends(check_permission("financial", "create"))):
    return await financial_controller.create_cvr(cvr_data)


@router.get("/cvr", response_model=List[CVR])
async def get_cvrs(project_id: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await financial_controller.get_cvrs(project_id)


@router.delete("/cvr/{cvr_id}")
async def delete_cvr(cvr_id: str, current_user: Employee = Depends(check_permission("financial", "delete"))):
    return await financial_controller.delete_cvr(cvr_id)


@router.post("/billing", response_model=Billing)
async def create_billing(billing_data: BillingCreate, current_user: Employee = Depends(check_permission("financial", "create"))):
    return await financial_controller.create_billing(billing_data)


@router.get("/billing", response_model=List[Billing])
async def get_billings(project_id: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await financial_controller.get_billings(project_id)


@router.put("/billing/{billing_id}/status")
async def update_billing_status(billing_id: str, status: str, current_user: Employee = Depends(check_permission("financial", "edit"))):
    return await financial_controller.update_billing_status(billing_id, status)


@router.get("/billing/{billing_id}")
async def get_billing(billing_id: str, current_user: Employee = Depends(check_permission("financial", "view"))):
    return await financial_controller.get_billing(billing_id)


@router.delete("/billing/{billing_id}")
async def delete_billing(billing_id: str, current_user: Employee = Depends(check_permission("financial", "delete"))):
    return await financial_controller.delete_billing(billing_id)


@router.patch("/billing/{billing_id}/status")
async def patch_billing_status(billing_id: str, data: BillingStatusUpdate, current_user: Employee = Depends(check_permission("financial", "edit"))):
    return await financial_controller.patch_billing_status(billing_id, data)


@router.get("/financial/dashboard")
async def get_financial_dashboard(current_user: Employee = Depends(check_permission("financial", "view"))):
    return await financial_controller.get_financial_dashboard()
