from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime, timezone


class ContractorRole(BaseModel):
    category: str


class ContractorCreate(BaseModel):
    name: str
    contractor_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    gstin: Optional[str] = None
    project_id: Optional[str] = None
    trade: Optional[str] = None
    contract_value: float = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"
    roles: List[ContractorRole] = Field(default_factory=list)
    notes: Optional[str] = None


class ContractorUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    gstin: Optional[str] = None
    project_id: Optional[str] = None
    trade: Optional[str] = None
    contract_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[ContractorRole]] = None
    notes: Optional[str] = None


class Contractor(ContractorCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None
