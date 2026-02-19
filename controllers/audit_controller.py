import math
import uuid
from datetime import datetime, timezone, timedelta
from database import db

IST = timezone(timedelta(hours=5, minutes=30))


def get_client_ip(request) -> str:
    """Get real client IP — checks X-Forwarded-For (proxy/nginx) first, then falls back to direct client IP."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else None


def get_user_agent(request) -> str:
    """Extract User-Agent header from request."""
    return request.headers.get("user-agent", "")


def parse_device(ua: str) -> dict:
    """Parse User-Agent string into OS, browser, and device type."""
    if not ua:
        return {"os": "Unknown", "browser": "Unknown", "device": "Unknown"}

    ua_lower = ua.lower()

    # Detect OS
    if "iphone" in ua_lower:
        os_name = "iOS"
    elif "ipad" in ua_lower:
        os_name = "iPadOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "windows" in ua_lower:
        os_name = "Windows"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "cros" in ua_lower:
        os_name = "ChromeOS"
    else:
        os_name = "Unknown"

    # Detect browser
    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "chrome" in ua_lower and "safari" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower:
        browser = "Safari"
    else:
        browser = "Unknown"

    # Detect device type
    if "mobile" in ua_lower or "iphone" in ua_lower or ("android" in ua_lower and "mobile" in ua_lower):
        device = "Mobile"
    elif "ipad" in ua_lower or "tablet" in ua_lower:
        device = "Tablet"
    else:
        device = "Desktop"

    return {"os": os_name, "browser": browser, "device": device}


async def log_audit(
    user_id: str,
    user_name: str,
    user_role: str,
    action: str,
    module: str,
    resource: str,
    description: str,
    resource_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
):
    """Fire-and-forget audit log entry — never raises."""
    try:
        device_info = parse_device(user_agent)
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "action": action,
            "module": module,
            "resource": resource,
            "resource_id": resource_id,
            "description": description,
            "ip_address": ip_address,
            "device": device_info,
            "timestamp": datetime.now(IST).isoformat(),
        })
    except Exception:
        pass  # audit must never break the main operation


async def get_audit_logs(
    page: int = 1,
    limit: int = 25,
    module: str = None,
    action: str = None,
    user_id: str = None,
    date_from: str = None,
    date_to: str = None,
    search: str = None,
):
    query = {}
    if module:
        query["module"] = module
    if action:
        query["action"] = action
    if user_id:
        query["user_id"] = user_id
    if date_from or date_to:
        ts = {}
        if date_from:
            ts["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            ts["$lte"] = datetime.fromisoformat(date_to + "T23:59:59")
        query["timestamp"] = ts
    if search:
        query["description"] = {"$regex": search, "$options": "i"}

    total = await db.audit_logs.count_documents(query)
    skip = (page - 1) * limit
    items = await db.audit_logs.find(query, {"_id": 0}) \
        .sort("timestamp", -1) \
        .skip(skip) \
        .limit(limit) \
        .to_list(limit)

    # convert datetime to IST string for JSON (MongoDB stores datetime in UTC internally)
    for item in items:
        ts = item.get("timestamp")
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            item["timestamp"] = ts.astimezone(IST).isoformat()

    return {
        "data": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if limit else 1,
        "limit": limit,
    }
