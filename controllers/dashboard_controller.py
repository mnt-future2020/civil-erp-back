from datetime import datetime, timezone, timedelta
from database import db


async def get_dashboard_stats() -> dict:
    # ── Projects ──────────────────────────────────────────
    total_projects = await db.projects.count_documents({})
    active_projects = await db.projects.count_documents({"status": "in_progress"})

    projects = await db.projects.find({}, {"_id": 0, "budget": 1, "actual_cost": 1}).to_list(1000)
    total_budget = sum(p.get('budget', 0) for p in projects)
    total_spent = sum(p.get('actual_cost', 0) for p in projects)

    this_month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
    projects_this_month = await db.projects.count_documents(
        {"created_at": {"$regex": f"^{this_month_prefix}"}}
    )

    # ── Tasks & SPI ───────────────────────────────────────
    total_tasks = await db.tasks.count_documents({})
    completed_tasks = await db.tasks.count_documents({"status": "completed"})
    in_progress_tasks = await db.tasks.count_documents({"status": "in_progress"})
    spi = round(completed_tasks / total_tasks, 2) if total_tasks > 0 else 1.0

    # ── Financial — Billing Pipeline ──────────────────────
    billing_pipeline = []
    for status in ["pending", "approved", "paid"]:
        docs = await db.billings.find(
            {"status": status}, {"_id": 0, "total_amount": 1}
        ).to_list(10000)
        count = len(docs)
        amount = sum(d.get("total_amount", 0) for d in docs)
        billing_pipeline.append({"status": status, "count": count, "amount": amount})

    total_billed = sum(b["amount"] for b in billing_pipeline)
    total_received = next((b["amount"] for b in billing_pipeline if b["status"] == "paid"), 0)
    pending_collection = total_billed - total_received

    # ── Procurement ───────────────────────────────────────
    total_vendors = await db.vendors.count_documents({"is_active": True})
    pending_pos = await db.purchase_orders.count_documents({"status": "pending"})
    approved_pos = await db.purchase_orders.count_documents({"status": "approved"})

    # Total PO value
    all_pos = await db.purchase_orders.find(
        {"status": {"$in": ["pending", "approved"]}},
        {"_id": 0, "total": 1}
    ).to_list(10000)
    active_po_value = sum(po.get("total", 0) for po in all_pos)

    # Recent POs (last 5)
    recent_pos_raw = await db.purchase_orders.find(
        {}, {"_id": 0, "id": 1, "po_number": 1, "vendor_id": 1, "total": 1, "status": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5).to_list(5)

    # Attach vendor names
    vendor_ids = list({po.get("vendor_id") for po in recent_pos_raw if po.get("vendor_id")})
    vendor_docs = await db.vendors.find(
        {"id": {"$in": vendor_ids}}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(200)
    vendor_map = {v["id"]: v["name"] for v in vendor_docs}

    recent_pos = [
        {
            "po_number": po.get("po_number", "—"),
            "vendor_name": vendor_map.get(po.get("vendor_id", ""), "—"),
            "total": po.get("total", 0),
            "status": po.get("status", "—"),
        }
        for po in recent_pos_raw
    ]

    # ── HRMS ──────────────────────────────────────────────
    total_employees = await db.employees.count_documents({"is_active": True})

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    present_today = await db.attendance.count_documents({"date": today_str, "status": "present"})
    absent_today = await db.attendance.count_documents({"date": today_str, "status": "absent"})

    # Payroll this month
    payroll_month = datetime.now(timezone.utc).strftime("%Y-%m")
    payroll_docs = await db.payroll.find(
        {"month": payroll_month}, {"_id": 0, "net_salary": 1, "status": 1}
    ).to_list(10000)
    payroll_processed = sum(p.get("net_salary", 0) for p in payroll_docs if p.get("status") == "paid")
    payroll_pending = sum(p.get("net_salary", 0) for p in payroll_docs if p.get("status") != "paid")
    payroll_count = len(payroll_docs)

    # ── Equipment ─────────────────────────────────────────
    total_equipment = await db.inventory.count_documents({"item_type": "equipment"})
    in_use_equipment = await db.inventory.count_documents(
        {"item_type": "equipment", "equipment_status": "in_use"}
    )
    equipment_utilization = round(in_use_equipment / total_equipment * 100, 1) if total_equipment > 0 else 0.0

    # ── Inventory / Stock Alerts ──────────────────────────
    low_stock_count = await db.inventory.count_documents(
        {"item_type": {"$ne": "equipment"}, "status": "low_stock"}
    )
    out_of_stock_count = await db.inventory.count_documents(
        {"item_type": {"$ne": "equipment"}, "status": "out_of_stock"}
    )
    alert_items_raw = await db.inventory.find(
        {"item_type": {"$ne": "equipment"}, "status": {"$in": ["low_stock", "out_of_stock"]}},
        {"_id": 0, "id": 1, "item_name": 1, "category": 1, "quantity": 1,
         "minimum_quantity": 1, "unit": 1, "status": 1, "project_id": 1}
    ).sort("status", 1).to_list(50)

    project_ids = list({item["project_id"] for item in alert_items_raw if item.get("project_id")})
    proj_docs = await db.projects.find(
        {"id": {"$in": project_ids}}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(200)
    proj_name_map = {p["id"]: p["name"] for p in proj_docs}

    stock_alerts = [
        {
            "id": item.get("id"),
            "item_name": item.get("item_name"),
            "category": item.get("category"),
            "quantity": item.get("quantity", 0),
            "minimum_quantity": item.get("minimum_quantity", 0),
            "unit": item.get("unit", ""),
            "status": item.get("status"),
            "project_name": proj_name_map.get(item.get("project_id", ""), "—")
        }
        for item in alert_items_raw
    ]

    # ── Recent Activity (last 7 audit logs) ───────────────
    recent_activity = await db.audit_logs.find(
        {}, {"_id": 0, "user_name": 1, "action": 1, "module": 1, "description": 1, "timestamp": 1}
    ).sort("timestamp", -1).limit(7).to_list(7)

    return {
        # Projects
        "total_projects": total_projects,
        "active_projects": active_projects,
        "projects_this_month": projects_this_month,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "budget_utilization": round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0.0,
        "cost_variance": total_budget - total_spent,
        # Tasks
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "spi": spi,
        # Financial
        "billing_pipeline": billing_pipeline,
        "total_billed": total_billed,
        "total_received": total_received,
        "pending_collection": pending_collection,
        # Procurement
        "total_vendors": total_vendors,
        "pending_pos": pending_pos,
        "approved_pos": approved_pos,
        "active_po_value": active_po_value,
        "recent_pos": recent_pos,
        # HRMS
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "payroll_processed": payroll_processed,
        "payroll_pending": payroll_pending,
        "payroll_count": payroll_count,
        # Equipment & Inventory
        "equipment_utilization": equipment_utilization,
        "total_equipment": total_equipment,
        "in_use_equipment": in_use_equipment,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "stock_alerts": stock_alerts,
        # Activity
        "recent_activity": recent_activity,
        # Legacy
        "safety_incidents": 0,
    }


async def get_chart_data() -> dict:
    # Per-project budget vs actual cost comparison (in Lakhs)
    projects = await db.projects.find(
        {}, {"_id": 0, "name": 1, "budget": 1, "actual_cost": 1}
    ).to_list(100)

    project_labels = [p.get("name", "Unknown") for p in projects]
    budget_series = [round(p.get("budget", 0) / 100000, 1) for p in projects]
    actual_series = [round(p.get("actual_cost", 0) / 100000, 1) for p in projects]

    # Project status distribution
    project_status = {
        "planning": await db.projects.count_documents({"status": "planning"}),
        "in_progress": await db.projects.count_documents({"status": "in_progress"}),
        "on_hold": await db.projects.count_documents({"status": "on_hold"}),
        "completed": await db.projects.count_documents({"status": "completed"})
    }

    return {
        "project_cost": {
            "labels": project_labels,
            "budget": budget_series,
            "actual": actual_series
        },
        "project_status": project_status
    }
