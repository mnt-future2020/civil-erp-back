from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from models.financial import CVR, CVRCreate, Billing, BillingCreate, BillingStatusUpdate
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import financial_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(tags=["financial"])


@router.post("/cvr", response_model=CVR)
async def create_cvr(cvr_data: CVRCreate, request: Request, current_user: Employee = Depends(check_permission("financial", "create"))):
    result = await financial_controller.create_cvr(cvr_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "financial", "cvr", "Created cost vs revenue entry", result.id, _ip(request), _ua(request))
    return result


@router.get("/cvr", response_model=List[CVR])
async def get_cvrs(project_id: Optional[str] = None, current_user: Employee = Depends(check_permission("financial", "view"))):
    return await financial_controller.get_cvrs(project_id)


@router.delete("/cvr/{cvr_id}")
async def delete_cvr(cvr_id: str, request: Request, current_user: Employee = Depends(check_permission("financial", "delete"))):
    result = await financial_controller.delete_cvr(cvr_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "financial", "cvr", "Deleted CVR entry", cvr_id, _ip(request), _ua(request))
    return result


@router.post("/billing", response_model=Billing)
async def create_billing(billing_data: BillingCreate, request: Request, current_user: Employee = Depends(check_permission("financial", "create"))):
    result = await financial_controller.create_billing(billing_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "financial", "billing", f"Created billing — ₹{billing_data.amount:,.2f}", result.id, _ip(request), _ua(request))
    return result


@router.get("/billing", response_model=List[Billing])
async def get_billings(project_id: Optional[str] = None, current_user: Employee = Depends(check_permission("financial", "view"))):
    return await financial_controller.get_billings(project_id)


@router.put("/billing/{billing_id}/status")
async def update_billing_status(billing_id: str, status: str, request: Request, current_user: Employee = Depends(check_permission("financial", "edit"))):
    result = await financial_controller.update_billing_status(billing_id, status)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "financial", "billing", f"Changed billing status to '{status}'", billing_id, _ip(request), _ua(request))
    return result


@router.get("/billing/{billing_id}")
async def get_billing(billing_id: str, current_user: Employee = Depends(check_permission("financial", "view"))):
    return await financial_controller.get_billing(billing_id)


@router.delete("/billing/{billing_id}")
async def delete_billing(billing_id: str, request: Request, current_user: Employee = Depends(check_permission("financial", "delete"))):
    result = await financial_controller.delete_billing(billing_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "financial", "billing", "Deleted billing", billing_id, _ip(request), _ua(request))
    return result


@router.patch("/billing/{billing_id}/status")
async def patch_billing_status(billing_id: str, data: BillingStatusUpdate, request: Request, current_user: Employee = Depends(check_permission("financial", "edit"))):
    result = await financial_controller.patch_billing_status(billing_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "financial", "billing", f"Changed billing status to '{data.status}'", billing_id, _ip(request), _ua(request))
    return result


@router.get("/financial/dashboard")
async def get_financial_dashboard(current_user: Employee = Depends(check_permission("financial", "view"))):
    return await financial_controller.get_financial_dashboard()
