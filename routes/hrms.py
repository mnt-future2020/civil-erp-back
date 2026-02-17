from fastapi import APIRouter, Depends
from typing import Optional
from models.hrms import Employee, EmployeeCreate, EmployeeUpdate, AttendanceCreate, PayrollCreate, PayrollStatusUpdate, LaborCategoryCreate, LaborCreate
from core.auth import get_current_user, check_permission
from controllers import hrms_controller

router = APIRouter(tags=["hrms"])


# ── Employees ─────────────────────────────────────────────

@router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate, current_user: Employee = Depends(check_permission("hrms", "create"))):
    return await hrms_controller.create_employee(employee_data)


@router.get("/employees")
async def get_employees(department: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_employees(department)


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_employee(employee_id)


@router.get("/employees/{employee_id}/detail")
async def get_employee_detail(employee_id: str, current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_employee_detail(employee_id)


@router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, employee_data: EmployeeUpdate, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    return await hrms_controller.update_employee(employee_id, employee_data)


@router.patch("/employees/{employee_id}/deactivate")
async def deactivate_employee(employee_id: str, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    return await hrms_controller.deactivate_employee(employee_id)


# ── Attendance ────────────────────────────────────────────

@router.post("/attendance")
async def create_attendance(attendance_data: AttendanceCreate, current_user: Employee = Depends(check_permission("hrms", "create"))):
    return await hrms_controller.create_attendance(attendance_data)


@router.get("/attendance")
async def get_attendance(employee_id: Optional[str] = None, project_id: Optional[str] = None, date: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_attendance(employee_id, project_id, date)


@router.delete("/attendance/{att_id}")
async def delete_attendance(att_id: str, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    return await hrms_controller.delete_attendance(att_id)


# ── Payroll ───────────────────────────────────────────────

@router.post("/payroll")
async def create_payroll(payroll_data: PayrollCreate, current_user: Employee = Depends(check_permission("hrms", "create"))):
    return await hrms_controller.create_payroll(payroll_data)


@router.get("/payroll")
async def get_payrolls(employee_id: Optional[str] = None, month: Optional[str] = None, status: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_payrolls(employee_id, month, status)


@router.patch("/payroll/{payroll_id}/status")
async def update_payroll_status(payroll_id: str, data: PayrollStatusUpdate, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    return await hrms_controller.update_payroll_status(payroll_id, data)


@router.delete("/payroll/{payroll_id}")
async def delete_payroll(payroll_id: str, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    return await hrms_controller.delete_payroll(payroll_id)


@router.get("/hrms/dashboard")
async def get_hrms_dashboard(current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_hrms_dashboard()


# ── Labor Categories ───────────────────────────────────────

@router.post("/labor-categories")
async def create_labor_category(data: LaborCategoryCreate, current_user: Employee = Depends(check_permission("hrms", "create"))):
    return await hrms_controller.create_labor_category(data)


@router.get("/labor-categories")
async def get_labor_categories(current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_labor_categories()


@router.delete("/labor-categories/{cat_id}")
async def delete_labor_category(cat_id: str, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    return await hrms_controller.delete_labor_category(cat_id)


# ── Labor Entries ──────────────────────────────────────────

@router.post("/labor")
async def create_labor(data: LaborCreate, current_user: Employee = Depends(check_permission("hrms", "create"))):
    return await hrms_controller.create_labor(data)


@router.get("/labor")
async def get_labor(project_id: Optional[str] = None, current_user: Employee = Depends(get_current_user)):
    return await hrms_controller.get_labor(project_id)


@router.put("/labor/{labor_id}")
async def update_labor(labor_id: str, data: LaborCreate, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    return await hrms_controller.update_labor(labor_id, data)


@router.delete("/labor/{labor_id}")
async def delete_labor(labor_id: str, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    return await hrms_controller.delete_labor(labor_id)
