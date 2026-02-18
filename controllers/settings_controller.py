from fastapi import HTTPException
from datetime import datetime, timezone
import httpx
import smtplib
from email.mime.text import MIMEText

from database import db
from models.settings import GSTCredentialsCreate, GSTCredentialsResponse, CloudinaryCredentials, SMTPCredentials, SMTPCredentialsResponse
from core.encryption import encrypt_value, decrypt_value


# ── GST Credentials ───────────────────────────────────────

async def save_gst_credentials(creds: GSTCredentialsCreate, current_user_id: str) -> dict:
    existing = await db.gst_settings.find_one({}, {"_id": 0})
    password_enc = encrypt_value(creds.password) if creds.password not in ("___unchanged___", "") else (existing or {}).get("password_enc", "")
    secret_enc = encrypt_value(creds.client_secret) if creds.client_secret != "___unchanged___" else (existing or {}).get("client_secret_enc", "")
    doc = {
        "gstin": creds.gstin,
        "username": creds.username,
        "password_enc": password_enc,
        "client_id": creds.client_id,
        "client_secret_enc": secret_enc,
        "nic_url": creds.nic_url,
        "is_sandbox": creds.is_sandbox,
        "updated_by": current_user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.gst_settings.update_one({}, {"$set": doc}, upsert=True)
    return {"message": "GST credentials saved", "gstin": creds.gstin}


async def get_gst_credentials() -> dict:
    settings = await db.gst_settings.find_one({}, {"_id": 0})
    if not settings:
        return {"is_configured": False}
    return GSTCredentialsResponse(
        gstin=settings["gstin"],
        username=settings["username"],
        client_id=settings["client_id"],
        nic_url=settings["nic_url"],
        is_sandbox=settings.get("is_sandbox", True),
        is_configured=True,
        last_updated=settings.get("updated_at")
    ).model_dump()


async def delete_gst_credentials() -> dict:
    await db.gst_settings.delete_many({})
    return {"message": "GST credentials deleted"}


async def test_gst_connection() -> dict:
    settings = await db.gst_settings.find_one({}, {"_id": 0})
    if not settings:
        raise HTTPException(status_code=400, detail="GST credentials not configured")
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
                    return {"status": "connected", "message": "NIC Portal connection successful"}
                return {"status": "auth_failed", "message": data.get("ErrorDetails", [{}])[0].get("ErrorMessage", "Authentication failed")}
            return {"status": "error", "message": f"NIC Portal returned status {auth_response.status_code}"}
    except httpx.ConnectError:
        return {"status": "unreachable", "message": "Cannot reach NIC portal. Check URL and network."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Cloudinary Credentials ────────────────────────────────

async def save_cloudinary_credentials(creds: CloudinaryCredentials, current_user_id: str) -> dict:
    existing = await db.cloudinary_settings.find_one({}, {"_id": 0})
    secret_enc = encrypt_value(creds.api_secret) if creds.api_secret != "___unchanged___" else (existing or {}).get("api_secret_enc", "")
    doc = {
        "cloud_name": creds.cloud_name,
        "api_key": creds.api_key,
        "api_secret_enc": secret_enc,
        "updated_by": current_user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.cloudinary_settings.update_one({}, {"$set": doc}, upsert=True)
    return {"message": "Cloudinary credentials saved"}


async def get_cloudinary_credentials() -> dict:
    settings = await db.cloudinary_settings.find_one({}, {"_id": 0})
    if not settings:
        return {"is_configured": False}
    return {
        "is_configured": True,
        "cloud_name": settings["cloud_name"],
        "api_key": settings["api_key"],
        "last_updated": settings.get("updated_at")
    }


async def delete_cloudinary_credentials() -> dict:
    await db.cloudinary_settings.delete_many({})
    return {"message": "Cloudinary credentials deleted"}


# ── SMTP Credentials ──────────────────────────────────────

async def save_smtp_credentials(creds: SMTPCredentials, current_user_id: str) -> dict:
    existing = await db.smtp_settings.find_one({}, {"_id": 0})
    password_enc = encrypt_value(creds.password) if creds.password not in ("___unchanged___", "") else (existing or {}).get("password_enc", "")
    doc = {
        "host": creds.host,
        "port": creds.port,
        "username": creds.username,
        "password_enc": password_enc,
        "from_email": creds.from_email,
        "from_name": creds.from_name,
        "use_tls": creds.use_tls,
        "updated_by": current_user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.smtp_settings.update_one({}, {"$set": doc}, upsert=True)
    return {"message": "SMTP credentials saved"}


async def get_smtp_credentials() -> dict:
    settings = await db.smtp_settings.find_one({}, {"_id": 0})
    if not settings:
        return {"is_configured": False}
    return SMTPCredentialsResponse(
        host=settings["host"],
        port=settings["port"],
        username=settings["username"],
        from_email=settings["from_email"],
        from_name=settings.get("from_name", "Civil ERP"),
        use_tls=settings.get("use_tls", True),
        is_configured=True,
        last_updated=settings.get("updated_at")
    ).model_dump()


async def delete_smtp_credentials() -> dict:
    await db.smtp_settings.delete_many({})
    return {"message": "SMTP credentials deleted"}


async def test_smtp_connection() -> dict:
    settings = await db.smtp_settings.find_one({}, {"_id": 0})
    if not settings:
        raise HTTPException(status_code=400, detail="SMTP credentials not configured")
    try:
        password = decrypt_value(settings["password_enc"])
        if settings.get("use_tls", True):
            server = smtplib.SMTP(settings["host"], settings["port"], timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings["host"], settings["port"], timeout=10)
        server.login(settings["username"], password)
        server.quit()
        return {"status": "connected", "message": f"SMTP connection to {settings['host']}:{settings['port']} successful"}
    except smtplib.SMTPAuthenticationError:
        return {"status": "auth_failed", "message": "Authentication failed. Check username and password."}
    except smtplib.SMTPConnectError:
        return {"status": "unreachable", "message": f"Cannot connect to {settings['host']}:{settings['port']}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def send_test_email(to_email: str) -> dict:
    settings = await db.smtp_settings.find_one({}, {"_id": 0})
    if not settings:
        raise HTTPException(status_code=400, detail="SMTP credentials not configured")
    try:
        password = decrypt_value(settings["password_enc"])
        from_addr = f"{settings.get('from_name', 'Civil ERP')} <{settings['from_email']}>"
        msg = MIMEText(
            "This is a test email from Civil ERP.\n\nYour SMTP configuration is working correctly.",
            "plain"
        )
        msg["Subject"] = "Civil ERP — SMTP Test Email"
        msg["From"] = from_addr
        msg["To"] = to_email
        if settings.get("use_tls", True):
            server = smtplib.SMTP(settings["host"], settings["port"], timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings["host"], settings["port"], timeout=10)
        server.login(settings["username"], password)
        server.sendmail(settings["from_email"], [to_email], msg.as_string())
        server.quit()
        return {"status": "sent", "message": f"Test email sent to {to_email}"}
    except smtplib.SMTPAuthenticationError:
        return {"status": "auth_failed", "message": "Authentication failed. Check username and password."}
    except smtplib.SMTPRecipientsRefused:
        return {"status": "error", "message": f"Recipient address {to_email} was refused."}
    except smtplib.SMTPConnectError:
        return {"status": "unreachable", "message": f"Cannot connect to {settings['host']}:{settings['port']}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_cloudinary_config() -> dict | None:
    settings = await db.cloudinary_settings.find_one({}, {"_id": 0})
    if not settings:
        return None
    try:
        return {
            "cloud_name": settings["cloud_name"],
            "api_key": settings["api_key"],
            "api_secret": decrypt_value(settings["api_secret_enc"])
        }
    except Exception:
        return None
