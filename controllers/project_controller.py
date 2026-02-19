from fastapi import HTTPException
from typing import Optional, List
from datetime import datetime, timezone

from database import db
from models.project import (
    Project, ProjectCreate, ProjectStatusUpdate, ProjectProgressUpdate,
    Task, TaskCreate, TaskStatusUpdate,
    DPR, DPRCreate
)
from models.hrms import Employee


# ── Projects ──────────────────────────────────────────────

async def create_project(project_data: ProjectCreate, current_user: Employee) -> Project:
    # Ensure project code is unique
    existing = await db.projects.find_one({"code": project_data.code}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail=f"Project code '{project_data.code}' already exists")
    project = Project(**project_data.model_dump(), created_by=current_user.id)
    await db.projects.insert_one(project.model_dump())
    return project


async def get_projects(page: int = 1, limit: int = 10, status: Optional[str] = None, search: Optional[str] = None) -> dict:
    query = {}
    if status and status != 'all':
        query['status'] = status
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'code': {'$regex': search, '$options': 'i'}},
            {'client_name': {'$regex': search, '$options': 'i'}},
        ]
    total = await db.projects.count_documents(query)
    skip = (page - 1) * limit
    data = await db.projects.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    pages = max(1, (total + limit - 1) // limit)
    return {"data": data, "total": total, "page": page, "pages": pages, "limit": limit}


async def get_project(project_id: str) -> Project:
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        # Fallback: try lookup by project code (for URL-friendly routes)
        project = await db.projects.find_one({"code": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**project)


async def update_project(project_id: str, project_data: ProjectCreate) -> Project:
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    # If code changed, check uniqueness
    if project_data.code != existing.get("code"):
        dup = await db.projects.find_one({"code": project_data.code, "id": {"$ne": project_id}}, {"_id": 0})
        if dup:
            raise HTTPException(status_code=400, detail=f"Project code '{project_data.code}' already exists")
    await db.projects.update_one({"id": project_id}, {"$set": project_data.model_dump()})
    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return Project(**updated)


async def delete_project(project_id: str) -> dict:
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}


async def update_project_status(project_id: str, data: ProjectStatusUpdate) -> dict:
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.projects.update_one({"id": project_id}, {"$set": {"status": data.status}})
    return await db.projects.find_one({"id": project_id}, {"_id": 0})


async def recalculate_project_progress(project_id: str):
    """Auto-calculate progress = (completed tasks / total tasks) * 100."""
    tasks = await db.tasks.find({"project_id": project_id}, {"status": 1}).to_list(1000)
    total = len(tasks)
    if total == 0:
        pct = 0.0
    else:
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        pct = round((completed / total) * 100, 1)
    await db.projects.update_one({"id": project_id}, {"$set": {"progress_percentage": pct}})
    return pct


async def update_project_progress(project_id: str, data: ProjectProgressUpdate) -> dict:
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    update = {}
    if data.actual_cost is not None:
        update["actual_cost"] = data.actual_cost
    if update:
        await db.projects.update_one({"id": project_id}, {"$set": update})
    return await db.projects.find_one({"id": project_id}, {"_id": 0})


async def get_project_summary(project_id: str) -> dict:
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = await db.tasks.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    dprs = await db.dprs.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    billings = await db.billings.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    cvrs = await db.cvrs.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    pos = await db.purchase_orders.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    attendance = await db.attendance.find({"project_id": project_id}, {"_id": 0}).to_list(1000)

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    in_progress_tasks = len([t for t in tasks if t.get('status') == 'in_progress'])

    # Sync progress_percentage from tasks
    pct = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0.0
    if project.get("progress_percentage") != pct:
        await db.projects.update_one({"id": project_id}, {"$set": {"progress_percentage": pct}})
        project["progress_percentage"] = pct
    total_billed = sum(b.get('total_amount', 0) for b in billings)
    total_po = sum(p.get('total', 0) for p in pos)
    total_cvr_work = sum(c.get('work_done_value', 0) for c in cvrs)
    labor_days = len([a for a in attendance if a.get('status') == 'present'])

    return {
        "project": project,
        "tasks": {"total": total_tasks, "completed": completed_tasks, "in_progress": in_progress_tasks, "pending": total_tasks - completed_tasks - in_progress_tasks},
        "dprs": {"total": len(dprs), "latest": dprs[-1] if dprs else None},
        "financial": {"total_billed": total_billed, "total_po_value": total_po, "total_cvr_work": total_cvr_work, "budget": project.get('budget', 0), "actual_cost": project.get('actual_cost', 0), "variance": project.get('budget', 0) - project.get('actual_cost', 0)},
        "workforce": {"labor_days": labor_days, "attendance_records": len(attendance)},
        "procurement": {"total_pos": len(pos), "total_po_value": total_po}
    }


# ── Tasks ─────────────────────────────────────────────────

async def create_task(task_data: TaskCreate) -> Task:
    task = Task(**task_data.model_dump())
    await db.tasks.insert_one(task.model_dump())
    await recalculate_project_progress(task_data.project_id)
    return task


async def get_tasks(project_id: Optional[str] = None) -> List[dict]:
    query = {"project_id": project_id} if project_id else {}
    return await db.tasks.find(query, {"_id": 0}).to_list(1000)


async def update_task(task_id: str, task_data: TaskCreate) -> Task:
    await db.tasks.update_one({"id": task_id}, {"$set": task_data.model_dump()})
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return Task(**updated)


async def update_task_status(task_id: str, data: TaskStatusUpdate) -> dict:
    existing = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    update = {"status": data.status}
    if data.progress is not None:
        update["progress"] = data.progress
    elif data.status == "completed":
        update["progress"] = 100.0
    await db.tasks.update_one({"id": task_id}, {"$set": update})
    await recalculate_project_progress(existing["project_id"])
    return await db.tasks.find_one({"id": task_id}, {"_id": 0})


async def delete_task(task_id: str) -> dict:
    existing = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.tasks.delete_one({"id": task_id})
    await recalculate_project_progress(existing["project_id"])
    return {"message": "Task deleted"}


# ── DPR ───────────────────────────────────────────────────

def _inv_status(qty, min_qty):
    if qty <= 0:
        return "out_of_stock"
    if min_qty > 0 and qty <= min_qty:
        return "low_stock"
    return "in_stock"


async def get_previous_closing_stock(project_id: str, inventory_id: str, current_date: str) -> float:
    """Get opening stock for an item: previous DPR's closing stock, or current inventory qty."""
    prev_dprs = await db.dprs.find(
        {
            "project_id": project_id,
            "date": {"$lt": current_date},
            "material_stock_entries.inventory_id": inventory_id
        },
        {"_id": 0, "material_stock_entries": 1, "date": 1}
    ).sort("date", -1).limit(1).to_list(1)

    if prev_dprs:
        for entry in prev_dprs[0].get("material_stock_entries", []):
            if entry.get("inventory_id") == inventory_id:
                return float(entry.get("closing_stock", 0))

    item = await db.inventory.find_one({"id": inventory_id}, {"_id": 0})
    if item:
        return float(item.get("quantity", 0))
    return 0.0


async def create_dpr(dpr_data: DPRCreate, current_user: Employee) -> DPR:
    dpr_dict = dpr_data.model_dump()

    # Resolve opening/closing stock for material_stock_entries
    resolved_material_entries = []
    for entry in dpr_data.material_stock_entries:
        inv_id = entry.get("inventory_id")
        received = float(entry.get("received", 0))
        used = float(entry.get("used", 0))
        opening = await get_previous_closing_stock(dpr_data.project_id, inv_id, dpr_data.date)
        closing = max(0.0, opening + received - used)
        resolved_material_entries.append({**entry, "opening_stock": opening, "closing_stock": closing})
    dpr_dict["material_stock_entries"] = resolved_material_entries

    dpr = DPR(**dpr_dict, created_by=current_user.id)
    await db.dprs.insert_one(dpr.model_dump())

    # IDs handled by new stock path (avoid double-deduction)
    new_path_ids = {e.get("inventory_id") for e in resolved_material_entries if e.get("inventory_id")}

    # Legacy: auto-deduct materials_used_entries (skip if handled by new path)
    for entry in dpr_data.materials_used_entries:
        item_id = entry.get("inventory_id")
        if item_id in new_path_ids:
            continue
        qty_used = float(entry.get("quantity_used", 0))
        if item_id and qty_used > 0:
            item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
            if item:
                new_qty = max(0, item["quantity"] - qty_used)
                await db.inventory.update_one({"id": item_id}, {"$set": {
                    "quantity": new_qty,
                    "total_value": new_qty * item.get("unit_price", 0),
                    "status": _inv_status(new_qty, item.get("minimum_quantity", 0)),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }})

    # New path: deduct used qty from material_stock_entries
    for entry in resolved_material_entries:
        item_id = entry.get("inventory_id")
        qty_used = float(entry.get("used", 0))
        if item_id and qty_used > 0:
            item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
            if item:
                new_qty = max(0, item["quantity"] - qty_used)
                await db.inventory.update_one({"id": item_id}, {"$set": {
                    "quantity": new_qty,
                    "total_value": new_qty * item.get("unit_price", 0),
                    "status": _inv_status(new_qty, item.get("minimum_quantity", 0)),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }})

    # Equipment: mark as in_use if hours > 0
    for entry in dpr_data.equipment_entries:
        item_id = entry.get("inventory_id")
        hours = float(entry.get("total_used_hours", 0))
        if item_id and hours > 0:
            await db.inventory.update_one({"id": item_id}, {"$set": {
                "equipment_status": "in_use",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }})

    return dpr


async def get_dprs(project_id: Optional[str] = None) -> List[dict]:
    query = {"project_id": project_id} if project_id else {}
    return await db.dprs.find(query, {"_id": 0}).to_list(1000)
