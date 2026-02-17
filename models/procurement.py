from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timezone


class VendorCreate(BaseModel):
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: str
    city: str
    state: str = "Tamil Nadu"
    pincode: str
    contact_person: str
    phone: str
    email: EmailStr
    category: str  # material, labor, equipment, subcontractor


class Vendor(VendorCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    rating: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VendorRating(BaseModel):
    rating: float


class POItemCreate(BaseModel):
    description: str
    unit: str
    quantity: float
    rate: Optional[float] = 0.0
    gst_rate: float = 18.0


class PurchaseOrderCreate(BaseModel):
    project_id: str
    vendor_id: str
    po_date: str
    delivery_date: str
    items: List[POItemCreate]
    terms: Optional[str] = None


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    po_number: str = ""
    project_id: str
    vendor_id: str
    po_date: str
    delivery_date: str
    items: List[Dict]
    terms: Optional[str] = None
    subtotal: float = 0.0
    gst_amount: float = 0.0
    total: float = 0.0
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class POStatusUpdate(BaseModel):
    status: str


class GRNItemCreate(BaseModel):
    po_item_index: int
    received_quantity: float
    remarks: Optional[str] = None


class GRNCreate(BaseModel):
    po_id: str
    grn_date: str
    items: List[GRNItemCreate]
    notes: Optional[str] = None


class GRN(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grn_number: str = ""
    po_id: str
    grn_date: str
    items: List[Dict]
    notes: Optional[str] = None
    status: str = "received"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
