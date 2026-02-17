from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timezone


class EInvoiceItemCreate(BaseModel):
    sl_no: int
    item_description: str
    hsn_code: str
    quantity: float
    unit: str = "NOS"
    unit_price: float
    discount: float = 0.0
    taxable_value: float
    gst_rate: float = 18.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    cess_amount: float = 0.0
    total_item_value: float = 0.0


class EInvoiceCreate(BaseModel):
    billing_id: Optional[str] = None
    supply_type: str = "B2B"
    document_type: str = "INV"
    document_number: str
    document_date: str
    seller_gstin: str
    seller_legal_name: str
    seller_trade_name: Optional[str] = None
    seller_address: str
    seller_location: str
    seller_pincode: str
    seller_state_code: str = "33"
    buyer_gstin: str
    buyer_legal_name: str
    buyer_trade_name: Optional[str] = None
    buyer_address: str
    buyer_location: str
    buyer_pincode: str
    buyer_state_code: str = "33"
    buyer_pos: str = "33"
    dispatch_from_name: Optional[str] = None
    dispatch_from_address: Optional[str] = None
    dispatch_from_location: Optional[str] = None
    dispatch_from_pincode: Optional[str] = None
    dispatch_from_state_code: Optional[str] = None
    ship_to_gstin: Optional[str] = None
    ship_to_legal_name: Optional[str] = None
    ship_to_address: Optional[str] = None
    ship_to_location: Optional[str] = None
    ship_to_pincode: Optional[str] = None
    ship_to_state_code: Optional[str] = None
    items: List[EInvoiceItemCreate]
    total_taxable_value: float
    total_cgst: float = 0.0
    total_sgst: float = 0.0
    total_igst: float = 0.0
    total_cess: float = 0.0
    total_discount: float = 0.0
    other_charges: float = 0.0
    round_off: float = 0.0
    total_invoice_value: float
    payment_mode: str = "CREDIT"
    payment_terms: Optional[str] = None
    transporter_id: Optional[str] = None
    transporter_name: Optional[str] = None
    transport_mode: Optional[str] = None
    transport_distance: Optional[int] = None
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None


class EInvoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    billing_id: Optional[str] = None
    document_number: str
    document_date: str
    document_type: str
    supply_type: str
    seller_gstin: str
    seller_legal_name: str
    buyer_gstin: str
    buyer_legal_name: str
    total_taxable_value: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_invoice_value: float
    items: List[Dict]
    irn: Optional[str] = None
    ack_number: Optional[str] = None
    ack_date: Optional[str] = None
    signed_invoice: Optional[str] = None
    signed_qr_code: Optional[str] = None
    qr_code_image: Optional[str] = None
    eway_bill_number: Optional[str] = None
    eway_bill_date: Optional[str] = None
    eway_bill_valid_till: Optional[str] = None
    status: str = "draft"
    nic_response: Optional[Dict] = None
    error_details: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None


class GSTINVerification(BaseModel):
    gstin: str
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    registration_date: Optional[str] = None
    constitution_of_business: Optional[str] = None
    taxpayer_type: Optional[str] = None
    gstin_status: Optional[str] = None
    state_jurisdiction: Optional[str] = None
    centre_jurisdiction: Optional[str] = None
    address: Optional[str] = None
    is_valid: bool = False
    verified_at: Optional[str] = None


class EWayBillCreate(BaseModel):
    einvoice_id: str
    transporter_id: str
    transporter_name: str
    transport_mode: str
    transport_distance: int
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None


class EWayBill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    einvoice_id: str
    eway_bill_number: str
    eway_bill_date: str
    valid_till: str
    transporter_id: str
    transporter_name: str
    transport_mode: str
    vehicle_number: Optional[str] = None
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
