from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime, timezone


class EmployeeBase(BaseModel):
    name: str
    employee_code: str
    email: EmailStr
    role: str
    designation: str
    department: str
    phone: str
    date_of_joining: str
    basic_salary: float
    hra: float = 0.0
    pf_number: Optional[str] = None
    esi_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc: Optional[str] = None
    avatar_url: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    password: str  # Required for creation - will be hashed before storage


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    employee_code: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # Optional - will be hashed if provided
    role: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    date_of_joining: Optional[str] = None
    basic_salary: Optional[float] = None
    hra: Optional[float] = None
    pf_number: Optional[str] = None
    esi_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc: Optional[str] = None


class Employee(EmployeeBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AttendanceCreate(BaseModel):
    employee_id: str
    project_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str = "present"  # present, absent, half_day, leave
    overtime_hours: float = 0.0


class Attendance(AttendanceCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PayrollCreate(BaseModel):
    employee_id: str
    month: str  # YYYY-MM
    basic_salary: float
    hra: float = 0.0
    overtime_pay: float = 0.0
    other_allowances: float = 0.0
    pf_deduction: float = 0.0
    esi_deduction: float = 0.0
    tds: float = 0.0
    other_deductions: float = 0.0


class Payroll(PayrollCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gross_salary: float = 0.0
    total_deductions: float = 0.0
    net_salary: float = 0.0
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PayrollStatusUpdate(BaseModel):
    status: str


# ── Labor ─────────────────────────────────────────────────

class LaborCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class LaborCategory(LaborCategoryCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LaborCreate(BaseModel):
    project_id: str
    category_id: str
    day_rate: float
    notes: Optional[str] = None


class Labor(LaborCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category_name: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
