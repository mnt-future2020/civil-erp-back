from fastapi import HTTPException
from typing import Optional
from datetime import datetime, timezone
import hashlib
import base64
import json
import qrcode
import secrets
import httpx
from io import BytesIO

from database import db
from models.einvoice import EInvoice, EInvoiceCreate
from core.encryption import decrypt_value


async def get_nic_auth_token():
    settings = await db.gst_settings.find_one({}, {"_id": 0})
    if not settings:
        return None, "GST credentials not configured. Go to Settings > GST Integration to set up."
    try:
        nic_url = settings["nic_url"]
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            auth_response = await client_http.post(
                f"{nic_url}/eivital/v1.04/auth",
                json={
                    "UserName": settings["username"],
                    "Password": decrypt_value(settings["password_enc"]),
                    "AppKey": settings["client_id"],
                    "ForceRefreshAccessToken": "true"
                },
                headers={
                    "client_id": settings["client_id"],
                    "client_secret": decrypt_value(settings["client_secret_enc"]),
                    "gstin": settings["gstin"]
                }
            )
            if auth_response.status_code == 200:
                data = auth_response.json()
                if data.get("Status") == 1:
                    return {
                        "token": data["Data"]["AuthToken"],
                        "sek": data["Data"]["Sek"],
                        "gstin": settings["gstin"],
                        "nic_url": nic_url
                    }, None
                error_msg = data.get("ErrorDetails", [{}])[0].get("ErrorMessage", "Auth failed")
                return None, error_msg
            return None, f"NIC auth returned {auth_response.status_code}"
    except Exception as e:
        return None, str(e)


def build_nic_invoice_payload(invoice_data: EInvoiceCreate) -> dict:
    items_list = []
    for item in invoice_data.items:
        items_list.append({
            "SlNo": str(item.sl_no),
            "PrdDesc": item.item_description,
            "IsServc": "N",
            "HsnCd": item.hsn_code,
            "Qty": item.quantity,
            "Unit": item.unit,
            "UnitPrice": item.unit_price,
            "Discount": item.discount,
            "TotAmt": item.quantity * item.unit_price,
            "AssAmt": item.taxable_value,
            "GstRt": item.gst_rate,
            "CgstAmt": item.cgst_amount,
            "SgstAmt": item.sgst_amount,
            "IgstAmt": item.igst_amount,
            "CesAmt": item.cess_amount,
            "TotItemVal": item.total_item_value
        })

    payload = {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": invoice_data.supply_type,
            "RegRev": "N",
            "IgstOnIntra": "N"
        },
        "DocDtls": {
            "Typ": invoice_data.document_type,
            "No": invoice_data.document_number,
            "Dt": invoice_data.document_date
        },
        "SellerDtls": {
            "Gstin": invoice_data.seller_gstin,
            "LglNm": invoice_data.seller_legal_name,
            "TrdNm": invoice_data.seller_trade_name or invoice_data.seller_legal_name,
            "Addr1": invoice_data.seller_address,
            "Loc": invoice_data.seller_location,
            "Pin": int(invoice_data.seller_pincode),
            "Stcd": invoice_data.seller_state_code
        },
        "BuyerDtls": {
            "Gstin": invoice_data.buyer_gstin,
            "LglNm": invoice_data.buyer_legal_name,
            "TrdNm": invoice_data.buyer_trade_name or invoice_data.buyer_legal_name,
            "Pos": invoice_data.buyer_pos,
            "Addr1": invoice_data.buyer_address,
            "Loc": invoice_data.buyer_location,
            "Pin": int(invoice_data.buyer_pincode),
            "Stcd": invoice_data.buyer_state_code
        },
        "ItemList": items_list,
        "ValDtls": {
            "AssVal": invoice_data.total_taxable_value,
            "CgstVal": invoice_data.total_cgst,
            "SgstVal": invoice_data.total_sgst,
            "IgstVal": invoice_data.total_igst,
            "CesVal": invoice_data.total_cess,
            "Discount": invoice_data.total_discount,
            "OthChrg": invoice_data.other_charges,
            "RndOffAmt": invoice_data.round_off,
            "TotInvVal": invoice_data.total_invoice_value
        },
        "PayDtls": {
            "Nm": invoice_data.buyer_legal_name,
            "Mode": invoice_data.payment_mode
        }
    }

    if invoice_data.dispatch_from_name:
        payload["DispDtls"] = {
            "Nm": invoice_data.dispatch_from_name,
            "Addr1": invoice_data.dispatch_from_address,
            "Loc": invoice_data.dispatch_from_location,
            "Pin": int(invoice_data.dispatch_from_pincode) if invoice_data.dispatch_from_pincode else 0,
            "Stcd": invoice_data.dispatch_from_state_code
        }

    if invoice_data.ship_to_gstin:
        payload["ShipDtls"] = {
            "Gstin": invoice_data.ship_to_gstin,
            "LglNm": invoice_data.ship_to_legal_name,
            "Addr1": invoice_data.ship_to_address,
            "Loc": invoice_data.ship_to_location,
            "Pin": int(invoice_data.ship_to_pincode) if invoice_data.ship_to_pincode else 0,
            "Stcd": invoice_data.ship_to_state_code
        }

    if invoice_data.transporter_id:
        payload["EwbDtls"] = {
            "TransId": invoice_data.transporter_id,
            "TransName": invoice_data.transporter_name,
            "TransMode": invoice_data.transport_mode,
            "Distance": invoice_data.transport_distance or 0,
            "VehNo": invoice_data.vehicle_number,
            "VehType": invoice_data.vehicle_type
        }

    return payload


def generate_qr_base64(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


async def generate_einvoice(invoice_data: EInvoiceCreate) -> dict:
    einvoice = EInvoice(
        billing_id=invoice_data.billing_id,
        document_number=invoice_data.document_number,
        document_date=invoice_data.document_date,
        document_type=invoice_data.document_type,
        supply_type=invoice_data.supply_type,
        seller_gstin=invoice_data.seller_gstin,
        seller_legal_name=invoice_data.seller_legal_name,
        buyer_gstin=invoice_data.buyer_gstin,
        buyer_legal_name=invoice_data.buyer_legal_name,
        total_taxable_value=invoice_data.total_taxable_value,
        total_cgst=invoice_data.total_cgst,
        total_sgst=invoice_data.total_sgst,
        total_igst=invoice_data.total_igst,
        total_invoice_value=invoice_data.total_invoice_value,
        items=[item.model_dump() for item in invoice_data.items],
        status="draft"
    )

    settings = await db.gst_settings.find_one({}, {"_id": 0})

    if settings:
        auth_result, auth_error = await get_nic_auth_token()
        if auth_error:
            einvoice.status = "auth_failed"
            einvoice.error_details = f"NIC Auth Failed: {auth_error}"
            doc = einvoice.model_dump()
            await db.e_invoices.insert_one(doc)
            doc.pop("_id", None)
            return doc
        try:
            nic_payload = build_nic_invoice_payload(invoice_data)
            nic_url = auth_result["nic_url"]
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                irn_response = await client_http.post(
                    f"{nic_url}/eicore/v1.03/Invoice",
                    json=nic_payload,
                    headers={
                        "client_id": settings["client_id"],
                        "client_secret": decrypt_value(settings["client_secret_enc"]),
                        "gstin": settings["gstin"],
                        "user_name": settings["username"],
                        "AuthToken": auth_result["token"],
                        "Sek": auth_result["sek"]
                    }
                )
                nic_data = irn_response.json()
                einvoice.nic_response = nic_data
                if nic_data.get("Status") == 1:
                    result_data = nic_data.get("Data", {})
                    einvoice.irn = result_data.get("Irn")
                    einvoice.ack_number = str(result_data.get("AckNo", ""))
                    einvoice.ack_date = result_data.get("AckDt")
                    einvoice.signed_invoice = result_data.get("SignedInvoice")
                    einvoice.signed_qr_code = result_data.get("SignedQRCode")
                    if einvoice.signed_qr_code:
                        einvoice.qr_code_image = generate_qr_base64(einvoice.signed_qr_code)
                    einvoice.status = "irn_generated"
                else:
                    errors = nic_data.get("ErrorDetails", [])
                    error_msg = "; ".join([e.get("ErrorMessage", "") for e in errors]) if errors else "Unknown NIC error"
                    einvoice.status = "rejected"
                    einvoice.error_details = error_msg
        except Exception as e:
            einvoice.status = "submission_failed"
            einvoice.error_details = f"NIC API Error: {str(e)}"
    else:
        simulated_irn = hashlib.sha256(f"{invoice_data.document_number}-{datetime.now().isoformat()}-{secrets.token_hex(8)}".encode()).hexdigest()
        einvoice.irn = simulated_irn
        einvoice.ack_number = str(hash(simulated_irn) % 1000000000)
        einvoice.ack_date = datetime.now(timezone.utc).strftime("%d/%m/%Y %I:%M:%S %p")
        qr_data = json.dumps({
            "SellerGstin": invoice_data.seller_gstin,
            "BuyerGstin": invoice_data.buyer_gstin,
            "DocNo": invoice_data.document_number,
            "DocDt": invoice_data.document_date,
            "TotVal": invoice_data.total_invoice_value,
            "Irn": simulated_irn,
            "IrnDt": einvoice.ack_date
        })
        einvoice.signed_qr_code = qr_data
        einvoice.qr_code_image = generate_qr_base64(qr_data)
        einvoice.status = "irn_generated"
        einvoice.nic_response = {"mode": "test", "message": "Generated in test mode (NIC credentials not configured)"}

    einvoice.updated_at = datetime.now(timezone.utc).isoformat()
    doc = einvoice.model_dump()
    await db.e_invoices.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_einvoices(status: Optional[str] = None) -> list:
    query = {}
    if status:
        query["status"] = status
    return await db.e_invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)


async def get_einvoice(einvoice_id: str) -> dict:
    invoice = await db.e_invoices.find_one({"id": einvoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="E-Invoice not found")
    return invoice


async def cancel_einvoice(einvoice_id: str, reason: str) -> dict:
    invoice = await db.e_invoices.find_one({"id": einvoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="E-Invoice not found")
    if invoice.get("status") != "irn_generated":
        raise HTTPException(status_code=400, detail="Only IRN-generated invoices can be cancelled")
    settings = await db.gst_settings.find_one({}, {"_id": 0})
    cancel_response = None
    if settings and invoice.get("irn"):
        auth_result, auth_error = await get_nic_auth_token()
        if not auth_error:
            try:
                nic_url = auth_result["nic_url"]
                async with httpx.AsyncClient(timeout=15.0) as client_http:
                    cancel_resp = await client_http.post(
                        f"{nic_url}/eicore/v1.03/Invoice/Cancel",
                        json={"Irn": invoice["irn"], "CnlRsn": "1", "CnlRem": reason},
                        headers={
                            "client_id": settings["client_id"],
                            "client_secret": decrypt_value(settings["client_secret_enc"]),
                            "gstin": settings["gstin"],
                            "user_name": settings["username"],
                            "AuthToken": auth_result["token"],
                            "Sek": auth_result["sek"]
                        }
                    )
                    cancel_response = cancel_resp.json()
            except Exception as e:
                cancel_response = {"error": str(e)}
    await db.e_invoices.update_one(
        {"id": einvoice_id},
        {"$set": {
            "status": "cancelled",
            "error_details": f"Cancelled: {reason}",
            "nic_response": cancel_response or {"mode": "test", "message": "Cancelled in test mode"},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return await db.e_invoices.find_one({"id": einvoice_id}, {"_id": 0})


async def get_einvoice_stats() -> dict:
    total = await db.e_invoices.count_documents({})
    irn_generated = await db.e_invoices.count_documents({"status": "irn_generated"})
    cancelled = await db.e_invoices.count_documents({"status": "cancelled"})
    failed = await db.e_invoices.count_documents({"status": {"$in": ["rejected", "auth_failed", "submission_failed"]}})
    draft = await db.e_invoices.count_documents({"status": "draft"})
    invoices = await db.e_invoices.find({}, {"_id": 0, "total_invoice_value": 1}).to_list(1000)
    total_value = sum(inv.get("total_invoice_value", 0) for inv in invoices)
    settings = await db.gst_settings.find_one({}, {"_id": 0})
    return {
        "total": total,
        "irn_generated": irn_generated,
        "cancelled": cancelled,
        "failed": failed,
        "draft": draft,
        "total_value": total_value,
        "credentials_configured": settings is not None
    }
