from fastapi import HTTPException
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from database import db
from models.hrms import (
    Employee, EmployeeCreate, EmployeeUpdate,
    Attendance, AttendanceCreate,
    Payroll, PayrollCreate, PayrollStatusUpdate,
    LaborCategory, LaborCategoryCreate, Labor, LaborCreate
)
from core.auth import get_password_hash


# ── Employees ─────────────────────────────────────────────

async def create_employee(employee_data: EmployeeCreate) -> Employee:
    existing = await db.employees.find_one({"email": employee_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    role = await db.roles.find_one({"name": employee_data.role})
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{employee_data.role}' does not exist")
    emp_dict = employee_data.model_dump()
    emp_dict['password'] = get_password_hash(emp_dict['password'])
    emp_dict['id'] = str(uuid.uuid4())
    emp_dict['is_active'] = True
    emp_dict['created_at'] = datetime.now(timezone.utc).isoformat()
    await db.employees.insert_one(emp_dict)
    return Employee(**{k: v for k, v in emp_dict.items() if k != 'password'})


async def get_employees(department: Optional[str] = None) -> List[dict]:
    query = {"is_active": True}
    if department:
        query["department"] = department
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    return employees


async def get_employee(employee_id: str) -> dict:
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


async def get_employee_detail(employee_id: str) -> dict:
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    att = await db.attendance.find({"employee_id": employee_id}, {"_id": 0}).sort("date", -1).to_list(1000)
    pays = await db.payrolls.find({"employee_id": employee_id}, {"_id": 0}).sort("month", -1).to_list(1000)
    present = len([a for a in att if a.get("status") == "present"])
    absent = len([a for a in att if a.get("status") == "absent"])
    half = len([a for a in att if a.get("status") == "half_day"])
    leave = len([a for a in att if a.get("status") == "leave"])
    total_ot = sum(a.get("overtime_hours", 0) for a in att)
    total_paid = sum(p.get("net_salary", 0) for p in pays)
    att_rate = round((present / len(att) * 100) if att else 0, 1)
    return {
        "employee": employee,
        "attendance": att[:30],
        "payrolls": pays,
        "stats": {
            "total_attendance": len(att), "present": present, "absent": absent,
            "half_day": half, "leave": leave, "attendance_rate": att_rate,
            "total_overtime": total_ot, "total_payrolls": len(pays), "total_paid": total_paid
        }
    }


async def update_employee(employee_id: str, employee_data: EmployeeUpdate) -> dict:
    existing = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    update_dict = employee_data.model_dump(exclude_unset=True)
    if "password" in update_dict and update_dict["password"]:
        update_dict["password"] = get_password_hash(update_dict["password"])
    if "role" in update_dict and update_dict["role"]:
        role = await db.roles.find_one({"name": update_dict["role"]})
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{update_dict['role']}' does not exist")
    if "email" in update_dict and update_dict["email"] != existing["email"]:
        email_exists = await db.employees.find_one({"email": update_dict["email"]})
        if email_exists:
            raise HTTPException(status_code=400, detail="Email already exists")
    await db.employees.update_one({"id": employee_id}, {"$set": update_dict})
    return await db.employees.find_one({"id": employee_id}, {"_id": 0})


async def deactivate_employee(employee_id: str) -> dict:
    existing = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    await db.employees.update_one({"id": employee_id}, {"$set": {"is_active": False}})
    return {"message": "Employee deactivated"}


# ── Attendance ────────────────────────────────────────────

async def create_attendance(attendance_data: AttendanceCreate) -> dict:
    attendance = Attendance(**attendance_data.model_dump())
    doc = attendance.model_dump()
    await db.attendance.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def get_attendance(employee_id: Optional[str] = None, project_id: Optional[str] = None, date: Optional[str] = None) -> List[dict]:
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if project_id:
        query["project_id"] = project_id
    if date:
        query["date"] = date
    return await db.attendance.find(query, {"_id": 0}).sort("date", -1).to_list(1000)


async def delete_attendance(att_id: str) -> dict:
    result = await db.attendance.delete_one({"id": att_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return {"message": "Deleted"}


# ── Payroll ───────────────────────────────────────────────

async def create_payroll(payroll_data: PayrollCreate) -> dict:
    payroll = Payroll(**payroll_data.model_dump())
    payroll.gross_salary = payroll.basic_salary + payroll.hra + payroll.overtime_pay + payroll.other_allowances
    payroll.total_deductions = payroll.pf_deduction + payroll.esi_deduction + payroll.tds + payroll.other_deductions
    payroll.net_salary = payroll.gross_salary - payroll.total_deductions
    doc = payroll.model_dump()
    await db.payrolls.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def get_payrolls(employee_id: Optional[str] = None, month: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if month:
        query["month"] = month
    if status:
        query["status"] = status
    return await db.payrolls.find(query, {"_id": 0}).to_list(1000)


async def update_payroll_status(payroll_id: str, data: PayrollStatusUpdate) -> dict:
    existing = await db.payrolls.find_one({"id": payroll_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Payroll not found")
    await db.payrolls.update_one({"id": payroll_id}, {"$set": {"status": data.status}})
    return await db.payrolls.find_one({"id": payroll_id}, {"_id": 0})


async def delete_payroll(payroll_id: str) -> dict:
    result = await db.payrolls.delete_one({"id": payroll_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Deleted"}


# ── HRMS Dashboard ────────────────────────────────────────

async def get_hrms_dashboard() -> dict:
    employees = await db.employees.find({"is_active": True}, {"_id": 0}).to_list(1000)
    attendance = await db.attendance.find({}, {"_id": 0}).to_list(5000)
    payrolls = await db.payrolls.find({}, {"_id": 0}).to_list(1000)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_att = [a for a in attendance if a.get("date") == today]
    present_today = len([a for a in today_att if a.get("status") == "present"])
    by_dept = {}
    for e in employees:
        d = e.get("department", "Other")
        by_dept[d] = by_dept.get(d, 0) + 1
    total_salary = sum(e.get("basic_salary", 0) + e.get("hra", 0) for e in employees)
    total_payroll = sum(p.get("net_salary", 0) for p in payrolls)
    pending_payrolls = len([p for p in payrolls if p.get("status") == "pending"])
    total_ot = sum(a.get("overtime_hours", 0) for a in attendance)
    all_present = len([a for a in attendance if a.get("status") == "present"])
    att_rate = round((all_present / len(attendance) * 100) if attendance else 0, 1)
    return {
        "employees": {"total": len(employees), "by_department": by_dept, "monthly_salary_budget": total_salary},
        "attendance": {"present_today": present_today, "total_today": len(today_att), "overall_rate": att_rate, "total_overtime": total_ot},
        "payroll": {"total_disbursed": total_payroll, "pending": pending_payrolls, "total_processed": len(payrolls)}
    }


# ── Labor Categories ───────────────────────────────────────

async def create_labor_category(data: LaborCategoryCreate) -> LaborCategory:
    existing = await db.labor_categories.find_one({"name": {"$regex": f"^{data.name}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = LaborCategory(**data.model_dump())
    await db.labor_categories.insert_one(cat.model_dump())
    return cat


async def get_labor_categories() -> List[dict]:
    return await db.labor_categories.find({}, {"_id": 0}).to_list(1000)


async def delete_labor_category(cat_id: str) -> dict:
    result = await db.labor_categories.delete_one({"id": cat_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


# ── Labor Entries ──────────────────────────────────────────

async def create_labor(data: LaborCreate) -> Labor:
    cat = await db.labor_categories.find_one({"id": data.category_id}, {"_id": 0})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    labor = Labor(**data.model_dump(), category_name=cat["name"])
    await db.labor.insert_one(labor.model_dump())
    return labor


async def get_labor(project_id: Optional[str] = None) -> List[dict]:
    query = {"project_id": project_id} if project_id else {}
    return await db.labor.find(query, {"_id": 0}).to_list(1000)


async def update_labor(labor_id: str, data: LaborCreate) -> dict:
    existing = await db.labor.find_one({"id": labor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Labor entry not found")
    cat = await db.labor_categories.find_one({"id": data.category_id}, {"_id": 0})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    update = {**data.model_dump(), "category_name": cat["name"]}
    await db.labor.update_one({"id": labor_id}, {"$set": update})
    return await db.labor.find_one({"id": labor_id}, {"_id": 0})


async def delete_labor(labor_id: str) -> dict:
    result = await db.labor.delete_one({"id": labor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Labor entry not found")
    return {"message": "Labor entry deleted"}
