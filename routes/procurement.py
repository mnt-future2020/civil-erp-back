from fastapi import APIRouter, Depends
from typing import List, Optional
from models.procurement import (
    Vendor, VendorCreate, VendorRating,
    PurchaseOrder, PurchaseOrderCreate, POStatusUpdate,
    GRN, GRNCreate
)
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import procurement_controller

router = APIRouter(tags=["procurement"])


# ── Vendors ───────────────────────────────────────────────

@router.post("/vendors", response_model=Vendor)
async def create_vendor(vendor_data: VendorCreate, current_user: Employee = Depends(check_permission("procurement", "create"))):
    return await procurement_controller.create_vendor(vendor_data)


@router.get("/vendors")
async def get_vendors(category: Optional[str] = None, page: int = 1, limit: int = 20, show_inactive: bool = False, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_vendors(category, page, limit, show_inactive)


@router.get("/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_vendor(vendor_id)


@router.get("/vendors/{vendor_id}/detail")
async def get_vendor_detail(vendor_id: str, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_vendor_detail(vendor_id)


@router.put("/vendors/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: str, vendor_data: VendorCreate, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    return await procurement_controller.update_vendor(vendor_id, vendor_data)


@router.patch("/vendors/{vendor_id}/rating")
async def rate_vendor(vendor_id: str, data: VendorRating, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    return await procurement_controller.rate_vendor(vendor_id, data)


@router.patch("/vendors/{vendor_id}/deactivate")
async def deactivate_vendor(vendor_id: str, current_user: Employee = Depends(check_permission("procurement", "delete"))):
    return await procurement_controller.deactivate_vendor(vendor_id)


@router.patch("/vendors/{vendor_id}/reactivate")
async def reactivate_vendor(vendor_id: str, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    return await procurement_controller.reactivate_vendor(vendor_id)


# ── Purchase Orders ───────────────────────────────────────

@router.post("/purchase-orders", response_model=PurchaseOrder)
async def create_purchase_order(po_data: PurchaseOrderCreate, current_user: Employee = Depends(check_permission("procurement", "create"))):
    return await procurement_controller.create_purchase_order(po_data)


@router.get("/purchase-orders")
async def get_purchase_orders(project_id: Optional[str] = None, vendor_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 10, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_purchase_orders(project_id, vendor_id, status, page, limit)


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_purchase_order(po_id)


@router.patch("/purchase-orders/{po_id}/status")
async def patch_po_status(po_id: str, data: POStatusUpdate, current_user: Employee = Depends(check_permission("procurement", "edit"))):
    return await procurement_controller.patch_po_status(po_id, data)


@router.delete("/purchase-orders/{po_id}")
async def delete_po(po_id: str, current_user: Employee = Depends(check_permission("procurement", "delete"))):
    return await procurement_controller.delete_po(po_id)


@router.get("/procurement/dashboard")
async def get_procurement_dashboard(current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_procurement_dashboard()


# ── GRN ───────────────────────────────────────────────────

@router.post("/grn", response_model=GRN)
async def create_grn(grn_data: GRNCreate, current_user: Employee = Depends(check_permission("procurement", "create"))):
    return await procurement_controller.create_grn(grn_data)


@router.get("/grn")
async def get_grns(po_id: Optional[str] = None, page: int = 1, limit: int = 10, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_grns(po_id, page, limit)


@router.get("/grn/{grn_id}")
async def get_grn(grn_id: str, current_user: Employee = Depends(get_current_user)):
    return await procurement_controller.get_grn_detail(grn_id)


@router.delete("/grn/{grn_id}")
async def delete_grn(grn_id: str, current_user: Employee = Depends(check_permission("procurement", "delete"))):
    return await procurement_controller.delete_grn(grn_id)
