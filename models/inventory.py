from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime, timezone


INVENTORY_CATEGORIES = [
    "Steel", "Cement", "Aggregates", "Sand", "Bricks",
    "Tiles", "Paint", "Plumbing", "Electrical", "Timber",
    "Hardware", "Glass", "Waterproofing", "Formwork", "Other"
]

INVENTORY_UNITS = [
    "MT", "Kg", "Bags", "Nos", "Sqft", "Sqm",
    "Rft", "Rmt", "Ltr", "Cum", "Sets", "Rolls"
]


class InventoryItemCreate(BaseModel):
    project_id: str
    item_name: str
    category: str
    unit: str
    quantity: float
    minimum_quantity: float = 0.0
    unit_price: float = 0.0
    gst_rate: float = 18.0
    hsn_code: Optional[str] = None
    location: Optional[str] = None       # Storage location on site
    vendor_id: Optional[str] = None
    notes: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    minimum_quantity: Optional[float] = None
    unit_price: Optional[float] = None
    gst_rate: Optional[float] = None
    hsn_code: Optional[str] = None
    location: Optional[str] = None
    vendor_id: Optional[str] = None
    notes: Optional[str] = None


class InventoryQuantityUpdate(BaseModel):
    quantity: float
    operation: str = "set"   # "set" | "add" | "subtract"
    notes: Optional[str] = None


class InventoryTransfer(BaseModel):
    from_item_id: str
    to_project_id: str
    to_item_id: Optional[str] = None   # None = create new item
    quantity: float
    notes: Optional[str] = None


class InventoryItem(InventoryItemCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_value: float = 0.0
    status: str = "in_stock"   # in_stock | low_stock | out_of_stock
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
