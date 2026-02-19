from fastapi import APIRouter, Depends, Request
from typing import Optional
from models.hrms import Employee, EmployeeCreate, EmployeeUpdate, AttendanceCreate, PayrollCreate, PayrollStatusUpdate, LaborCategoryCreate, LaborCreate
from core.auth import check_permission
from controllers import hrms_controller
from controllers.audit_controller import log_audit, get_client_ip as _ip, get_user_agent as _ua

router = APIRouter(tags=["hrms"])


# ── Employees ─────────────────────────────────────────────

@router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await hrms_controller.create_employee(employee_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "hrms", "employee", f"Created employee '{employee_data.name}'", result.id, _ip(request), _ua(request))
    return result


@router.get("/employees")
async def get_employees(department: Optional[str] = None, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_employees(department)


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_employee(employee_id)


@router.get("/employees/{employee_id}/detail")
async def get_employee_detail(employee_id: str, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_employee_detail(employee_id)


@router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, employee_data: EmployeeUpdate, request: Request, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    result = await hrms_controller.update_employee(employee_id, employee_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "hrms", "employee", f"Updated employee '{employee_data.name}'", employee_id, _ip(request), _ua(request))
    return result


@router.patch("/employees/{employee_id}/deactivate")
async def deactivate_employee(employee_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await hrms_controller.deactivate_employee(employee_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "hrms", "employee", "Deactivated employee", employee_id, _ip(request), _ua(request))
    return result


# ── Attendance ────────────────────────────────────────────

@router.post("/attendance")
async def create_attendance(attendance_data: AttendanceCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await hrms_controller.create_attendance(attendance_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "hrms", "attendance", f"Marked attendance for {attendance_data.date}", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.get("/attendance")
async def get_attendance(employee_id: Optional[str] = None, project_id: Optional[str] = None, date: Optional[str] = None, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_attendance(employee_id, project_id, date)


@router.delete("/attendance/{att_id}")
async def delete_attendance(att_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await hrms_controller.delete_attendance(att_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "hrms", "attendance", "Deleted attendance record", att_id, _ip(request), _ua(request))
    return result


# ── Payroll ───────────────────────────────────────────────

@router.post("/payroll")
async def create_payroll(payroll_data: PayrollCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await hrms_controller.create_payroll(payroll_data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "hrms", "payroll", f"Created payroll for {payroll_data.month}", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.get("/payroll")
async def get_payrolls(employee_id: Optional[str] = None, month: Optional[str] = None, status: Optional[str] = None, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_payrolls(employee_id, month, status)


@router.patch("/payroll/{payroll_id}/status")
async def update_payroll_status(payroll_id: str, data: PayrollStatusUpdate, request: Request, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    result = await hrms_controller.update_payroll_status(payroll_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "hrms", "payroll", f"Changed payroll status to '{data.status}'", payroll_id, _ip(request), _ua(request))
    return result


@router.delete("/payroll/{payroll_id}")
async def delete_payroll(payroll_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await hrms_controller.delete_payroll(payroll_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "hrms", "payroll", "Deleted payroll", payroll_id, _ip(request), _ua(request))
    return result


@router.get("/hrms/dashboard")
async def get_hrms_dashboard(current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_hrms_dashboard()


# ── Labor Categories ───────────────────────────────────────

@router.post("/labor-categories")
async def create_labor_category(data: LaborCategoryCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await hrms_controller.create_labor_category(data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "hrms", "labor_category", f"Created labor category '{data.name}'", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.get("/labor-categories")
async def get_labor_categories(current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_labor_categories()


@router.delete("/labor-categories/{cat_id}")
async def delete_labor_category(cat_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await hrms_controller.delete_labor_category(cat_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "hrms", "labor_category", "Deleted labor category", cat_id, _ip(request), _ua(request))
    return result


# ── Labor Entries ──────────────────────────────────────────

@router.post("/labor")
async def create_labor(data: LaborCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "create"))):
    result = await hrms_controller.create_labor(data)
    await log_audit(current_user.id, current_user.name, current_user.role, "CREATE", "hrms", "labor", "Created labor entry", ip_address=_ip(request), user_agent=_ua(request))
    return result


@router.get("/labor")
async def get_labor(project_id: Optional[str] = None, current_user: Employee = Depends(check_permission("hrms", "view"))):
    return await hrms_controller.get_labor(project_id)


@router.put("/labor/{labor_id}")
async def update_labor(labor_id: str, data: LaborCreate, request: Request, current_user: Employee = Depends(check_permission("hrms", "edit"))):
    result = await hrms_controller.update_labor(labor_id, data)
    await log_audit(current_user.id, current_user.name, current_user.role, "UPDATE", "hrms", "labor", "Updated labor entry", labor_id, _ip(request), _ua(request))
    return result


@router.delete("/labor/{labor_id}")
async def delete_labor(labor_id: str, request: Request, current_user: Employee = Depends(check_permission("hrms", "delete"))):
    result = await hrms_controller.delete_labor(labor_id)
    await log_audit(current_user.id, current_user.name, current_user.role, "DELETE", "hrms", "labor", "Deleted labor entry", labor_id, _ip(request), _ua(request))
    return result
