from fastapi import HTTPException
from typing import Optional, List
from datetime import datetime, timezone
import math
import re
import uuid
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database import db

logger = logging.getLogger(__name__)
from models.procurement import (
    Vendor, VendorCreate, VendorRating,
    PurchaseOrder, PurchaseOrderCreate, POStatusUpdate,
    GRN, GRNCreate
)
from core.encryption import decrypt_value


async def _send_po_approval_email(po: dict) -> None:
    """Send PO approval email to vendor. Silently skips if SMTP not configured."""
    smtp = await db.smtp_settings.find_one({}, {"_id": 0})
    if not smtp:
        return
    vendor = await db.vendors.find_one({"id": po.get("vendor_id")}, {"_id": 0})
    if not vendor or not vendor.get("email"):
        return
    project = await db.projects.find_one({"id": po.get("project_id")}, {"_id": 0})
    project_name = project.get("name", "") if project else ""

    # Build items HTML table
    rows = ""
    for i, item in enumerate(po.get("items", []), 1):
        amount = item.get("quantity", 0) * item.get("rate", 0)
        rows += (
            f"<tr style='background:{('#f9f9f9' if i%2==0 else '#fff')}'>"
            f"<td style='padding:8px;border:1px solid #ddd'>{i}</td>"
            f"<td style='padding:8px;border:1px solid #ddd'>{item.get('description','')}</td>"
            f"<td style='padding:8px;border:1px solid #ddd;text-align:center'>{item.get('unit','')}</td>"
            f"<td style='padding:8px;border:1px solid #ddd;text-align:right'>{item.get('quantity',0)}</td>"
            f"<td style='padding:8px;border:1px solid #ddd;text-align:right'>₹{item.get('rate',0):,.2f}</td>"
            f"<td style='padding:8px;border:1px solid #ddd;text-align:right'>₹{amount:,.2f}</td>"
            f"</tr>"
        )

    html = f"""
    <html><body style='font-family:Arial,sans-serif;color:#333;max-width:700px;margin:auto'>
    <div style='background:#1a56db;color:#fff;padding:20px 24px;border-radius:4px 4px 0 0'>
        <h2 style='margin:0'>Purchase Order Approved</h2>
        <p style='margin:4px 0 0;opacity:.85'>Civil ERP</p>
    </div>
    <div style='padding:24px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 4px 4px'>
        <p>Dear <strong>{vendor.get('name','Vendor')}</strong>,</p>
        <p>Please find below the details of the approved Purchase Order.</p>
        <table style='width:100%;border-collapse:collapse;margin:16px 0'>
            <tr><td style='padding:6px 12px;width:40%;color:#666'>PO Number</td><td style='padding:6px 12px;font-weight:bold'>{po.get('po_number','')}</td></tr>
            <tr style='background:#f9f9f9'><td style='padding:6px 12px;color:#666'>Project</td><td style='padding:6px 12px'>{project_name}</td></tr>
            <tr><td style='padding:6px 12px;color:#666'>PO Date</td><td style='padding:6px 12px'>{po.get('po_date','')}</td></tr>
            <tr style='background:#f9f9f9'><td style='padding:6px 12px;color:#666'>Delivery Date</td><td style='padding:6px 12px'>{po.get('delivery_date','')}</td></tr>
        </table>
        <h4 style='margin:16px 0 8px'>Items</h4>
        <table style='width:100%;border-collapse:collapse;font-size:13px'>
            <thead><tr style='background:#1a56db;color:#fff'>
                <th style='padding:8px;border:1px solid #ddd'>#</th>
                <th style='padding:8px;border:1px solid #ddd'>Description</th>
                <th style='padding:8px;border:1px solid #ddd'>Unit</th>
                <th style='padding:8px;border:1px solid #ddd'>Qty</th>
                <th style='padding:8px;border:1px solid #ddd'>Rate</th>
                <th style='padding:8px;border:1px solid #ddd'>Amount</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <table style='width:240px;margin:12px 0 12px auto;font-size:13px'>
            <tr><td style='padding:4px 8px;color:#666'>Subtotal</td><td style='padding:4px 8px;text-align:right'>₹{po.get('subtotal',0):,.2f}</td></tr>
            <tr><td style='padding:4px 8px;color:#666'>GST {f"({round(po.get('gst_amount',0)/po.get('subtotal',1)*100,2):.4g}%)" if po.get('subtotal',0) > 0 else ''}</td><td style='padding:4px 8px;text-align:right'>₹{po.get('gst_amount',0):,.2f}</td></tr>
            <tr style='font-weight:bold;background:#f0f4ff'><td style='padding:6px 8px;border-top:2px solid #1a56db'>Total</td><td style='padding:6px 8px;text-align:right;border-top:2px solid #1a56db'>₹{po.get('total',0):,.2f}</td></tr>
        </table>
        {f"<p style='font-size:13px;color:#555'><strong>Terms:</strong> {po.get('terms')}</p>" if po.get('terms') else ''}
        <p style='margin-top:24px;color:#555;font-size:13px'>Please acknowledge receipt of this PO and confirm the delivery schedule.</p>
        <p style='margin-top:16px;color:#888;font-size:12px'>This is an automated message from Civil ERP.</p>
    </div></body></html>
    """

    try:
        password = decrypt_value(smtp["password_enc"])
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Purchase Order Approved: {po.get('po_number','')} — {project_name}"
        msg["From"] = f"{smtp.get('from_name','Civil ERP')} <{smtp['from_email']}>"
        msg["To"] = vendor["email"]
        msg.attach(MIMEText(html, "html"))

        if smtp.get("use_tls", True):
            server = smtplib.SMTP(smtp["host"], smtp["port"], timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp["host"], smtp["port"], timeout=10)
        server.login(smtp["username"], password)
        server.sendmail(smtp["from_email"], [vendor["email"]], msg.as_string())
        server.quit()
        logger.info(f"PO approval email sent to {vendor['email']} for PO {po.get('po_number')}")
    except Exception as e:
        logger.error(f"PO approval email failed for PO {po.get('po_number')} → {vendor.get('email')}: {e}")


# ── Vendors ───────────────────────────────────────────────

async def create_vendor(vendor_data: VendorCreate) -> Vendor:
    vendor = Vendor(**vendor_data.model_dump())
    await db.vendors.insert_one(vendor.model_dump())
    return vendor


async def get_vendors(category: Optional[str] = None, page: int = 1, limit: int = 20, show_inactive: bool = False) -> dict:
    query = {} if show_inactive else {"is_active": True}
    if category:
        query["category"] = category
    total = await db.vendors.count_documents(query)
    skip = (page - 1) * limit
    items = await db.vendors.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {
        "data": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if limit else 1,
        "limit": limit,
    }


async def get_vendor(vendor_id: str) -> Vendor:
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return Vendor(**vendor)


async def get_vendor_detail(vendor_id: str) -> dict:
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    pos = await db.purchase_orders.find({"vendor_id": vendor_id}, {"_id": 0}).to_list(1000)
    grns = await db.grns.find({}, {"_id": 0}).to_list(1000)
    po_ids = {po.get("id") for po in pos}
    vendor_grns = [g for g in grns if g.get("po_id") in po_ids]
    total_po_value = sum(po.get("total", 0) for po in pos)
    po_by_status = {}
    for po in pos:
        s = po.get("status", "pending")
        po_by_status[s] = po_by_status.get(s, 0) + 1
    return {
        "vendor": vendor,
        "purchase_orders": pos,
        "grns": vendor_grns,
        "stats": {
            "total_pos": len(pos),
            "total_po_value": total_po_value,
            "total_grns": len(vendor_grns),
            "po_by_status": po_by_status,
            "avg_po_value": round(total_po_value / len(pos)) if pos else 0
        }
    }


async def update_vendor(vendor_id: str, vendor_data: VendorCreate) -> Vendor:
    await db.vendors.update_one({"id": vendor_id}, {"$set": vendor_data.model_dump()})
    updated = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return Vendor(**updated)


async def rate_vendor(vendor_id: str, data: VendorRating) -> dict:
    existing = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await db.vendors.update_one({"id": vendor_id}, {"$set": {"rating": data.rating}})
    return await db.vendors.find_one({"id": vendor_id}, {"_id": 0})


async def deactivate_vendor(vendor_id: str) -> dict:
    existing = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await db.vendors.update_one({"id": vendor_id}, {"$set": {"is_active": False}})
    return {"message": "Vendor deactivated"}


async def reactivate_vendor(vendor_id: str) -> dict:
    existing = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await db.vendors.update_one({"id": vendor_id}, {"$set": {"is_active": True}})
    return {"message": "Vendor reactivated"}


# ── Purchase Orders ───────────────────────────────────────

async def create_purchase_order(po_data: PurchaseOrderCreate) -> PurchaseOrder:
    count = await db.purchase_orders.count_documents({})
    po_number = f"PO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    items = [item.model_dump() for item in po_data.items]
    subtotal = sum(item['quantity'] * item['rate'] for item in items)
    gst_amount = sum(item['quantity'] * item['rate'] * (item.get('gst_rate', 18.0) / 100) for item in items)
    po = PurchaseOrder(
        po_number=po_number, project_id=po_data.project_id, vendor_id=po_data.vendor_id,
        po_date=po_data.po_date, delivery_date=po_data.delivery_date, items=items,
        terms=po_data.terms, subtotal=subtotal, gst_amount=gst_amount, total=subtotal + gst_amount
    )
    await db.purchase_orders.insert_one(po.model_dump())
    return po


async def get_purchase_orders(project_id: Optional[str] = None, vendor_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 20) -> dict:
    query = {}
    if project_id:
        query["project_id"] = project_id
    if vendor_id:
        query["vendor_id"] = vendor_id
    if status:
        query["status"] = status
    total = await db.purchase_orders.count_documents(query)
    skip = (page - 1) * limit
    items = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    # Enrich each PO with vendor_name and project_name
    vids = list({po.get("vendor_id") for po in items if po.get("vendor_id")})
    pids = list({po.get("project_id") for po in items if po.get("project_id")})
    vdocs = await db.vendors.find({"id": {"$in": vids}}, {"_id": 0, "id": 1, "name": 1}).to_list(200)
    pdocs = await db.projects.find({"id": {"$in": pids}}, {"_id": 0, "id": 1, "name": 1}).to_list(200)
    vmap = {v["id"]: v["name"] for v in vdocs}
    pmap = {p["id"]: p["name"] for p in pdocs}
    for po in items:
        po["vendor_name"] = vmap.get(po.get("vendor_id", ""), "")
        po["project_name"] = pmap.get(po.get("project_id", ""), "")
    return {
        "data": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if limit else 1,
        "limit": limit,
    }


async def get_purchase_order(po_id: str) -> dict:
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    vendor = await db.vendors.find_one({"id": po.get("vendor_id")}, {"_id": 0})
    project = await db.projects.find_one({"id": po.get("project_id")}, {"_id": 0})
    grns = await db.grns.find({"po_id": po_id}, {"_id": 0}).to_list(100)
    total_ordered = {i: item.get("quantity", 0) for i, item in enumerate(po.get("items", []))}
    total_received = {}
    for grn in grns:
        for gi in grn.get("items", []):
            idx = gi.get("po_item_index", 0)
            total_received[idx] = total_received.get(idx, 0) + gi.get("received_quantity", 0)
    matching = []
    for i, item in enumerate(po.get("items", [])):
        ordered = item.get("quantity", 0)
        received = total_received.get(i, 0)
        matching.append({
            "item_index": i,
            "description": item.get("description"),
            "ordered": ordered,
            "received": received,
            "pending": ordered - received,
            "status": "complete" if received >= ordered else "partial" if received > 0 else "pending"
        })
    return {"po": po, "vendor": vendor, "project": project, "grns": grns, "matching": matching}


async def patch_po_status(po_id: str, data: POStatusUpdate) -> dict:
    existing = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="PO not found")
    await db.purchase_orders.update_one({"id": po_id}, {"$set": {"status": data.status}})
    updated = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if data.status == "approved":
        await _send_po_approval_email(updated)
    return updated


async def delete_po(po_id: str) -> dict:
    result = await db.purchase_orders.delete_one({"id": po_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="PO not found")
    return {"message": "PO deleted"}


async def get_procurement_dashboard() -> dict:
    vendors = await db.vendors.find({"is_active": True}, {"_id": 0}).to_list(1000)
    pos = await db.purchase_orders.find({}, {"_id": 0}).to_list(1000)
    grns = await db.grns.find({}, {"_id": 0}).to_list(1000)
    total_po_value = sum(po.get("total", 0) for po in pos)
    pending_pos = len([p for p in pos if p.get("status") == "pending"])
    approved_pos = len([p for p in pos if p.get("status") == "approved"])
    by_category = {}
    for v in vendors:
        c = v.get("category", "other")
        by_category[c] = by_category.get(c, 0) + 1
    vendor_po_map = {}
    for po in pos:
        vid = po.get("vendor_id")
        vendor_po_map[vid] = vendor_po_map.get(vid, 0) + po.get("total", 0)
    top_vendor_id = max(vendor_po_map, key=vendor_po_map.get) if vendor_po_map else None
    top_vendor = next((v for v in vendors if v.get("id") == top_vendor_id), None) if top_vendor_id else None
    return {
        "vendors": {"total": len(vendors), "by_category": by_category},
        "purchase_orders": {"total": len(pos), "total_value": total_po_value, "pending": pending_pos, "approved": approved_pos, "delivered": len([p for p in pos if p.get("status") == "delivered"]), "closed": len([p for p in pos if p.get("status") == "closed"])},
        "grns": {"total": len(grns)},
        "top_vendor": {"name": top_vendor.get("name") if top_vendor else "-", "value": vendor_po_map.get(top_vendor_id, 0) if top_vendor_id else 0}
    }


# ── GRN ───────────────────────────────────────────────────

def _inventory_status(qty: float, min_qty: float) -> str:
    if qty <= 0:
        return "out_of_stock"
    if min_qty > 0 and qty <= min_qty:
        return "low_stock"
    return "in_stock"


async def create_grn(grn_data: GRNCreate) -> GRN:
    po = await db.purchase_orders.find_one({"id": grn_data.po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    existing_grns = await db.grns.find({"po_id": grn_data.po_id}, {"_id": 0}).to_list(1000)
    for grn_item in grn_data.items:
        po_item_index = grn_item.po_item_index
        if po_item_index >= len(po['items']):
            raise HTTPException(status_code=400, detail=f"Invalid PO item index: {po_item_index}")
        po_item = po['items'][po_item_index]
        po_quantity = po_item['quantity']
        total_received = 0.0
        for existing_grn in existing_grns:
            for item in existing_grn.get('items', []):
                if item.get('po_item_index') == po_item_index:
                    total_received += item.get('received_quantity', 0.0)
        new_total = total_received + grn_item.received_quantity
        if new_total > po_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot receive {grn_item.received_quantity} of '{po_item['description']}'. PO quantity: {po_quantity}, Already received: {total_received}, Remaining: {po_quantity - total_received}"
            )
    count = await db.grns.count_documents({})
    grn_number = f"GRN-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    items = [item.model_dump() for item in grn_data.items]
    grn = GRN(grn_number=grn_number, po_id=grn_data.po_id, grn_date=grn_data.grn_date, items=items, notes=grn_data.notes)
    await db.grns.insert_one(grn.model_dump())

    # ── Auto-sync inventory stock ──────────────────────────
    project_id = po.get("project_id")
    vendor_id = po.get("vendor_id")
    now = datetime.now(timezone.utc).isoformat()

    for grn_item in grn_data.items:
        po_item = po["items"][grn_item.po_item_index]
        item_name = po_item.get("description", "")
        unit = po_item.get("unit", "Nos")
        unit_price = po_item.get("rate", 0.0)
        received_qty = grn_item.received_quantity

        # Find existing inventory item in the same project (case-insensitive name match)
        existing = await db.inventory.find_one(
            {"project_id": project_id,
             "item_name": {"$regex": f"^{re.escape(item_name)}$", "$options": "i"}},
            {"_id": 0}
        )

        if existing:
            new_qty = existing["quantity"] + received_qty
            min_qty = existing.get("minimum_quantity", 0.0)
            eff_price = existing.get("unit_price") or unit_price
            await db.inventory.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "quantity": new_qty,
                    "total_value": round(new_qty * eff_price, 2),
                    "status": _inventory_status(new_qty, min_qty),
                    "vendor_id": vendor_id or existing.get("vendor_id"),
                    "updated_at": now,
                }}
            )
        else:
            total_val = round(received_qty * unit_price, 2)
            new_item = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "item_name": item_name,
                "category": "Other",
                "unit": unit,
                "quantity": received_qty,
                "minimum_quantity": 0.0,
                "unit_price": unit_price,
                "total_value": total_val,
                "hsn_code": None,
                "location": None,
                "vendor_id": vendor_id,
                "notes": f"Auto-created from GRN {grn_number}",
                "status": "in_stock",
                "created_by": None,
                "created_at": now,
                "updated_at": None,
            }
            await db.inventory.insert_one(new_item)

    return grn


async def get_grns(po_id: Optional[str] = None, page: int = 1, limit: int = 20) -> dict:
    query = {"po_id": po_id} if po_id else {}
    total = await db.grns.count_documents(query)
    skip = (page - 1) * limit
    items = await db.grns.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    # Enrich with PO number
    po_ids = list({g.get("po_id") for g in items if g.get("po_id")})
    po_docs = await db.purchase_orders.find({"id": {"$in": po_ids}}, {"_id": 0, "id": 1, "po_number": 1}).to_list(200)
    po_map = {p["id"]: p["po_number"] for p in po_docs}
    for g in items:
        g["po_number"] = po_map.get(g.get("po_id", ""), "")
    return {
        "data": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if limit else 1,
        "limit": limit,
    }


async def get_grn_detail(grn_id: str) -> dict:
    grn = await db.grns.find_one({"id": grn_id}, {"_id": 0})
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    po = await db.purchase_orders.find_one({"id": grn["po_id"]}, {"_id": 0})
    vendor = await db.vendors.find_one({"id": po.get("vendor_id")}, {"_id": 0}) if po else None
    project = await db.projects.find_one({"id": po.get("project_id")}, {"_id": 0}) if po else None
    po_items = (po or {}).get("items", [])
    enriched = []
    for item in grn.get("items", []):
        idx = item.get("po_item_index", 0)
        po_item = po_items[idx] if idx < len(po_items) else {}
        enriched.append({
            **item,
            "description": po_item.get("description", ""),
            "unit": po_item.get("unit", ""),
            "ordered_quantity": po_item.get("quantity", 0),
            "rate": po_item.get("rate", 0),
        })
    return {"grn": {**grn, "items": enriched}, "po": po, "vendor": vendor, "project": project}


async def delete_grn(grn_id: str) -> dict:
    result = await db.grns.delete_one({"id": grn_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="GRN not found")
    return {"message": "GRN deleted"}
