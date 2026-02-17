from fastapi import APIRouter, Depends
from typing import List
from models.compliance import GSTReturn, GSTReturnCreate, RERAProject, RERAProjectCreate
from models.hrms import Employee
from core.auth import get_current_user, check_permission
from controllers import compliance_controller

router = APIRouter(tags=["compliance"])


@router.post("/gst-returns", response_model=GSTReturn)
async def create_gst_return(gst_data: GSTReturnCreate, current_user: Employee = Depends(check_permission("compliance", "create"))):
    return await compliance_controller.create_gst_return(gst_data)


@router.get("/gst-returns", response_model=List[GSTReturn])
async def get_gst_returns(current_user: Employee = Depends(check_permission("compliance", "view"))):
    return await compliance_controller.get_gst_returns()


@router.post("/rera-projects", response_model=RERAProject)
async def create_rera_project(rera_data: RERAProjectCreate, current_user: Employee = Depends(check_permission("compliance", "create"))):
    return await compliance_controller.create_rera_project(rera_data)


@router.get("/rera-projects", response_model=List[RERAProject])
async def get_rera_projects(current_user: Employee = Depends(get_current_user)):
    return await compliance_controller.get_rera_projects()
