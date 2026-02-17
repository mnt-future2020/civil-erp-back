from fastapi import HTTPException
from typing import Optional, List

from database import db
from models.financial import CVR, CVRCreate, Billing, BillingCreate, BillingStatusUpdate


# ── CVR ───────────────────────────────────────────────────

async def create_cvr(cvr_data: CVRCreate) -> CVR:
    cvr = CVR(**cvr_data.model_dump())
    cvr.variance = cvr.contracted_value - cvr.work_done_value
    await db.cvrs.insert_one(cvr.model_dump())
    return cvr


async def get_cvrs(project_id: Optional[str] = None) -> List[dict]:
    query = {"project_id": project_id} if project_id else {}
    return await db.cvrs.find(query, {"_id": 0}).to_list(1000)


async def delete_cvr(cvr_id: str) -> dict:
    result = await db.cvrs.delete_one({"id": cvr_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="CVR not found")
    return {"message": "CVR deleted"}


# ── Billing ───────────────────────────────────────────────

async def create_billing(billing_data: BillingCreate) -> Billing:
    billing = Billing(**billing_data.model_dump())
    billing.gst_amount = billing.amount * billing.gst_rate / 100
    billing.total_amount = billing.amount + billing.gst_amount
    await db.billings.insert_one(billing.model_dump())
    return billing


async def get_billings(project_id: Optional[str] = None) -> List[dict]:
    query = {"project_id": project_id} if project_id else {}
    return await db.billings.find(query, {"_id": 0}).to_list(1000)


async def update_billing_status(billing_id: str, status: str) -> dict:
    await db.billings.update_one({"id": billing_id}, {"$set": {"status": status}})
    return {"message": "Status updated"}


async def get_billing(billing_id: str) -> dict:
    bill = await db.billings.find_one({"id": billing_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


async def delete_billing(billing_id: str) -> dict:
    result = await db.billings.delete_one({"id": billing_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"message": "Bill deleted"}


async def patch_billing_status(billing_id: str, data: BillingStatusUpdate) -> dict:
    existing = await db.billings.find_one({"id": billing_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Bill not found")
    await db.billings.update_one({"id": billing_id}, {"$set": {"status": data.status}})
    return await db.billings.find_one({"id": billing_id}, {"_id": 0})


# ── Financial Dashboard ───────────────────────────────────

async def get_financial_dashboard() -> dict:
    billings = await db.billings.find({}, {"_id": 0}).to_list(1000)
    cvrs = await db.cvrs.find({}, {"_id": 0}).to_list(1000)
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)

    total_billed = sum(b.get('total_amount', 0) for b in billings)
    total_gst = sum(b.get('gst_amount', 0) for b in billings)
    pending_amount = sum(b.get('total_amount', 0) for b in billings if b.get('status') == 'pending')
    approved_amount = sum(b.get('total_amount', 0) for b in billings if b.get('status') == 'approved')
    paid_amount = sum(b.get('total_amount', 0) for b in billings if b.get('status') == 'paid')
    total_received = sum(c.get('received_value', 0) for c in cvrs)
    total_retention = sum(c.get('retention_held', 0) for c in cvrs)
    total_contracted = sum(c.get('contracted_value', 0) for c in cvrs)
    total_work_done = sum(c.get('work_done_value', 0) for c in cvrs)
    total_budget = sum(p.get('budget', 0) for p in projects)
    total_spent = sum(p.get('actual_cost', 0) for p in projects)

    collection_eff = round((total_received / total_billed * 100) if total_billed > 0 else 0, 1)
    cpi = round((total_work_done / total_spent) if total_spent > 0 else 0, 2)

    project_breakdown = []
    for p in projects:
        pid = p.get('id')
        p_bills = [b for b in billings if b.get('project_id') == pid]
        p_cvrs = [c for c in cvrs if c.get('project_id') == pid]
        project_breakdown.append({
            "project_id": pid,
            "project_name": p.get('name'),
            "budget": p.get('budget', 0),
            "actual_cost": p.get('actual_cost', 0),
            "total_billed": sum(b.get('total_amount', 0) for b in p_bills),
            "bills_count": len(p_bills),
            "received": sum(c.get('received_value', 0) for c in p_cvrs),
            "variance": p.get('budget', 0) - p.get('actual_cost', 0)
        })

    bills_by_status = {"pending": 0, "approved": 0, "paid": 0}
    for b in billings:
        s = b.get('status', 'pending')
        bills_by_status[s] = bills_by_status.get(s, 0) + 1

    bills_by_type = {"running": 0, "final": 0, "advance": 0}
    for b in billings:
        t = b.get('bill_type', 'running')
        bills_by_type[t] = bills_by_type.get(t, 0) + 1

    return {
        "summary": {
            "total_billed": total_billed,
            "total_gst": total_gst,
            "pending_collection": pending_amount,
            "approved_amount": approved_amount,
            "paid_amount": paid_amount,
            "total_received": total_received,
            "total_retention": total_retention,
            "collection_efficiency": collection_eff,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_contracted": total_contracted,
            "total_work_done": total_work_done,
            "cpi": cpi,
            "total_bills": len(billings),
            "total_cvrs": len(cvrs)
        },
        "bills_by_status": bills_by_status,
        "bills_by_type": bills_by_type,
        "project_breakdown": sorted(project_breakdown, key=lambda x: x['total_billed'], reverse=True)
    }
