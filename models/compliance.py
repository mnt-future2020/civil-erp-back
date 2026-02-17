from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime, timezone


class GSTReturnCreate(BaseModel):
    return_type: str  # GSTR-1, GSTR-3B
    period: str  # YYYY-MM
    total_outward_supplies: float = 0.0
    total_inward_supplies: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    itc_claimed: float = 0.0


class GSTReturn(GSTReturnCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tax_payable: float = 0.0
    status: str = "draft"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RERAProjectCreate(BaseModel):
    project_id: str
    rera_number: str
    registration_date: str
    validity_date: str
    escrow_bank: str
    escrow_account: str
    total_units: int
    sold_units: int = 0


class RERAProject(RERAProjectCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    compliance_status: str = "compliant"
    last_quarterly_update: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
