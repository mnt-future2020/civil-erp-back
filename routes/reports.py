from fastapi import APIRouter, Depends
from typing import Optional
from models.hrms import Employee
from core.auth import check_permission
from controllers import reports_controller

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/executive-summary")
async def get_executive_summary(current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_executive_summary()


@router.get("/project-analysis")
async def get_project_analysis(project_id: Optional[str] = None, current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_project_analysis(project_id)


@router.get("/financial-summary")
async def get_financial_summary(start_date: Optional[str] = None, end_date: Optional[str] = None, current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_financial_summary(start_date, end_date)


@router.get("/procurement-analysis")
async def get_procurement_analysis(current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_procurement_analysis()


@router.get("/hrms-summary")
async def get_hrms_summary(month: Optional[str] = None, current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_hrms_summary(month)


@router.get("/compliance-status")
async def get_compliance_status(current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_compliance_status()


@router.get("/cost-variance")
async def get_cost_variance_report(current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.get_cost_variance_report()


@router.get("/export/{report_type}")
async def export_report(report_type: str, format: str = "excel", current_user: Employee = Depends(check_permission("reports", "view"))):
    return await reports_controller.export_report(report_type, format)
