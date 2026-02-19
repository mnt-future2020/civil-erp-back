from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from models.procurement import (
    Vendor, VendorCreate, VendorRating,
    PurchaseOrder, PurchaseOrderCreate, POStatusUpdate,
    GRN, GRNCreate
)
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import procurement_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(tags=["procurement"])


# ── Vendors ───────────────────────────────────────────────

@router.post("/vendors", response_model=Vendor)
async def create_vendor(vendor_data: VendorCreate, request: Request, current_user: Employee = Depends(check_permission("procurement", "create"))):
    result = await procurement_controller.create_vendor(vendor_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "procurement", "vendor", f"Created vendor '{vendor_data.name}'", result.id, _ip(request), _ua(request))
    return result


@router.get("/vendors")
async def get_vendors(category: Optional[str] = None, page: int = 1, limit: int = 20, show_inactive: bool = False, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_vendors(category, page, limit, show_inactive)


@router.get("/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_vendor(vendor_id)


@router.get("/vendors/{vendor_id}/detail")
async def get_vendor_detail(vendor_id: str, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_vendor_detail(vendor_id)


@router.put("/vendors/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: str, vendor_data: VendorCreate, request: Request, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    result = await procurement_controller.update_vendor(vendor_id, vendor_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "procurement", "vendor", f"Updated vendor '{vendor_data.name}'", vendor_id, _ip(request), _ua(request))
    return result


@router.patch("/vendors/{vendor_id}/rating")
async def rate_vendor(vendor_id: str, data: VendorRating, request: Request, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    result = await procurement_controller.rate_vendor(vendor_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "procurement", "vendor", f"Rated vendor {data.rating} stars", vendor_id, _ip(request), _ua(request))
    return result


@router.patch("/vendors/{vendor_id}/deactivate")
async def deactivate_vendor(vendor_id: str, request: Request, current_user: Employee = Depends(check_permission("procurement", "delete"))):
    result = await procurement_controller.deactivate_vendor(vendor_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "procurement", "vendor", "Deactivated vendor", vendor_id, _ip(request), _ua(request))
    return result


@router.patch("/vendors/{vendor_id}/reactivate")
async def reactivate_vendor(vendor_id: str, request: Request, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    result = await procurement_controller.reactivate_vendor(vendor_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "procurement", "vendor", "Reactivated vendor", vendor_id, _ip(request), _ua(request))
    return result


# ── Purchase Orders ───────────────────────────────────────

@router.post("/purchase-orders", response_model=PurchaseOrder)
async def create_purchase_order(po_data: PurchaseOrderCreate, request: Request, current_user: Employee = Depends(check_permission("procurement", "create"))):
    result = await procurement_controller.create_purchase_order(po_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "procurement", "purchase_order", f"Created PO '{result.po_number}' — ₹{result.total:,.2f}", result.id, _ip(request), _ua(request))
    return result


@router.get("/purchase-orders")
async def get_purchase_orders(project_id: Optional[str] = None, vendor_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 10, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_purchase_orders(project_id, vendor_id, status, page, limit)


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_purchase_order(po_id)


@router.patch("/purchase-orders/{po_id}/status")
async def patch_po_status(po_id: str, data: POStatusUpdate, request: Request, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    result = await procurement_controller.patch_po_status(po_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "procurement", "purchase_order", f"Changed PO status to '{data.status}'", po_id, _ip(request), _ua(request))
    return result


@router.delete("/purchase-orders/{po_id}")
async def delete_po(po_id: str, request: Request, current_user: Employee = Depends(check_permission("procurement", "delete"))):
    result = await procurement_controller.delete_po(po_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "procurement", "purchase_order", "Deleted purchase order", po_id, _ip(request), _ua(request))
    return result


@router.get("/procurement/dashboard")
async def get_procurement_dashboard(current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_procurement_dashboard()


# ── GRN ───────────────────────────────────────────────────

@router.post("/grn", response_model=GRN)
async def create_grn(grn_data: GRNCreate, request: Request, current_user: Employee = Depends(check_permission("procurement", "create"))):
    result = await procurement_controller.create_grn(grn_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "procurement", "grn", f"Created GRN '{result.grn_number}'", result.id, _ip(request), _ua(request))
    return result


@router.get("/grn")
async def get_grns(po_id: Optional[str] = None, page: int = 1, limit: int = 10, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_grns(po_id, page, limit)


@router.get("/grn/{grn_id}")
async def get_grn(grn_id: str, current_user: Employee = Depends(check_permission("procurement", "view"))):
    return await procurement_controller.get_grn_detail(grn_id)


@router.delete("/grn/{grn_id}")
async def delete_grn(grn_id: str, request: Request, current_user: Employee = Depends(check_permission("procurement", "delete"))):
    result = await procurement_controller.delete_grn(grn_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "procurement", "grn", "Deleted GRN", grn_id, _ip(request), _ua(request))
    return result
