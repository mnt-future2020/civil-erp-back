from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime, timezone


class CVRCreate(BaseModel):
    project_id: str
    period_start: str
    period_end: str
    contracted_value: float
    work_done_value: float
    billed_value: float
    received_value: float
    retention_held: float = 0.0
    notes: Optional[str] = None


class CVR(CVRCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    variance: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BillingCreate(BaseModel):
    project_id: str
    bill_number: str
    bill_date: str
    description: str
    amount: float
    gst_rate: float = 18.0
    bill_type: str = "running"  # running, final, advance


class Billing(BillingCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gst_amount: float = 0.0
    total_amount: float = 0.0
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BillingStatusUpdate(BaseModel):
    status: str
