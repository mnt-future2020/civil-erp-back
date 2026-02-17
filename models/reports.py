from pydantic import BaseModel
from typing import Optional


class ReportFilters(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    project_id: Optional[str] = None
    vendor_id: Optional[str] = None
    employee_id: Optional[str] = None
    status: Optional[str] = None
