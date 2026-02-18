from fastapi import APIRouter, Depends
from typing import List, Optional
from models.project import (
    Project, ProjectCreate, ProjectStatusUpdate, ProjectProgressUpdate,
    Task, TaskCreate, TaskStatusUpdate,
    DPR, DPRCreate
)
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import project_controller

router = APIRouter(tags=["projects"])


# ── Projects ──────────────────────────────────────────────

@router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: Employee = Depends(check_permission("projects", "create"))):
    return await project_controller.create_project(project_data, current_user)


@router.get("/projects")
async def get_projects(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Employee = Depends(get_current_user)
):
    return await project_controller.get_projects(page, limit, status, search)


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: Employee = Depends(get_current_user)):
    return await project_controller.get_project(project_id)


@router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_data: ProjectCreate, current_user: Employee = Depends(check_permission("projects", "edit"))):
    return await project_controller.update_project(project_id, project_data)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: Employee = Depends(check_permission("projects", "delete"))):
    return await project_controller.delete_project(project_id)


@router.patch("/projects/{project_id}/status")
async def update_project_status(project_id: str, data: ProjectStatusUpdate, current_user: Employee = Depends(check_permission("projects", "edit"))):
    return await project_controller.update_project_status(project_id, data)


@router.patch("/projects/{project_id}/progress")
async def update_project_progress(project_id: str, data: ProjectProgressUpdate, current_user: Employee = Depends(check_permission("projects", "edit"))):
    return await project_controller.update_project_progress(project_id, data)


@router.get("/projects/{project_id}/summary")
async def get_project_summary(project_id: str, current_user: Employee = Depends(get_current_user)):
    return await project_controller.get_project_summary(project_id)


# ── Tasks ─────────────────────────────────────────────────

@router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, current_user: Employee = Depends(check_permission("projects", "create"))):
    return await project_controller.create_task(task_data)


@router.get("/tasks", response_model=List[Task])
async def get_tasks(project_id: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await project_controller.get_tasks(project_id)


@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_data: TaskCreate, current_user: Employee = Depends(check_permission("projects", "edit"))):
    return await project_controller.update_task(task_id, task_data)


@router.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, data: TaskStatusUpdate, current_user: Employee = Depends(check_permission("projects", "edit"))):
    return await project_controller.update_task_status(task_id, data)


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: Employee = Depends(check_permission("projects", "delete"))):
    return await project_controller.delete_task(task_id)


# ── DPR ───────────────────────────────────────────────────

@router.post("/dpr", response_model=DPR)
async def create_dpr(dpr_data: DPRCreate, current_user: Employee = Depends(check_permission("projects", "create"))):
    return await project_controller.create_dpr(dpr_data, current_user)


@router.get("/dpr", response_model=List[DPR])
async def get_dprs(project_id: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await project_controller.get_dprs(project_id)


@router.get("/dpr/opening-stock")
async def get_opening_stock(project_id: str, inventory_id: str, date: str, current_user: Employee = Depends(get_current_user)):
    stock = await project_controller.get_previous_closing_stock(project_id, inventory_id, date)
    return {"opening_stock": stock}
