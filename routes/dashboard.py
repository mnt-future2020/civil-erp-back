from fastapi import APIRouter, Depends
from models.hrms import Employee
from core.auth import check_permission
from controllers import dashboard_controller

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(current_user: Employee = Depends(check_permission("dashboard", "view"))):
    return await dashboard_controller.get_dashboard_stats()


@router.get("/chart-data")
async def get_chart_data(current_user: Employee = Depends(check_permission("dashboard", "view"))):
    return await dashboard_controller.get_chart_data()
