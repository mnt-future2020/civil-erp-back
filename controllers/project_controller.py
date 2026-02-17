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
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**project)


async def update_project(project_id: str, project_data: ProjectCreate) -> Project:
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
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


async def update_project_progress(project_id: str, data: ProjectProgressUpdate) -> dict:
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    update = {"progress_percentage": data.progress_percentage}
    if data.actual_cost is not None:
        update["actual_cost"] = data.actual_cost
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
    return await db.tasks.find_one({"id": task_id}, {"_id": 0})


async def delete_task(task_id: str) -> dict:
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}


# ── DPR ───────────────────────────────────────────────────

def _inv_status(qty, min_qty):
    if qty <= 0:
        return "out_of_stock"
    if min_qty > 0 and qty <= min_qty:
        return "low_stock"
    return "in_stock"


async def create_dpr(dpr_data: DPRCreate, current_user: Employee) -> DPR:
    dpr = DPR(**dpr_data.model_dump(), created_by=current_user.id)
    await db.dprs.insert_one(dpr.model_dump())
    # Auto-deduct inventory for each material used
    for entry in dpr_data.materials_used_entries:
        item_id = entry.get("inventory_id")
        qty_used = float(entry.get("quantity_used", 0))
        if item_id and qty_used > 0:
            item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
            if item:
                new_qty = max(0, item["quantity"] - qty_used)
                await db.inventory.update_one({"id": item_id}, {"$set": {
                    "quantity": new_qty,
                    "total_value": new_qty * item["unit_price"],
                    "status": _inv_status(new_qty, item["minimum_quantity"]),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }})
    return dpr


async def get_dprs(project_id: Optional[str] = None) -> List[dict]:
    query = {"project_id": project_id} if project_id else {}
    return await db.dprs.find(query, {"_id": 0}).to_list(1000)
