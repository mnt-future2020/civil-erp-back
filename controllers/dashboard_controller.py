from datetime import datetime, timezone
from database import db


async def get_dashboard_stats() -> dict:
    total_projects = await db.projects.count_documents({})
    active_projects = await db.projects.count_documents({"status": "in_progress"})
    total_vendors = await db.vendors.count_documents({"is_active": True})
    total_employees = await db.employees.count_documents({"is_active": True})

    projects = await db.projects.find({}, {"_id": 0, "budget": 1, "actual_cost": 1}).to_list(1000)
    total_budget = sum(p.get('budget', 0) for p in projects)
    total_spent = sum(p.get('actual_cost', 0) for p in projects)

    pending_pos = await db.purchase_orders.count_documents({"status": "pending"})

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    present_today = await db.attendance.count_documents({"date": today_str, "status": "present"})

    # Projects created this month
    this_month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
    projects_this_month = await db.projects.count_documents(
        {"created_at": {"$regex": f"^{this_month_prefix}"}}
    )

    # SPI — ratio of completed tasks to total tasks (simplified)
    total_tasks = await db.tasks.count_documents({})
    completed_tasks = await db.tasks.count_documents({"status": "completed"})
    spi = round(completed_tasks / total_tasks, 2) if total_tasks > 0 else 1.0

    # Equipment utilization from inventory
    total_equipment = await db.inventory.count_documents({"item_type": "equipment"})
    in_use_equipment = await db.inventory.count_documents(
        {"item_type": "equipment", "equipment_status": "in_use"}
    )
    equipment_utilization = round(in_use_equipment / total_equipment * 100, 1) if total_equipment > 0 else 0.0

    # Stock alerts — low_stock and out_of_stock items (exclude equipment)
    # Use $ne instead of exact match so older docs without item_type field are also included
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

    # Attach project name to each alert item
    project_ids = list({item["project_id"] for item in alert_items_raw if item.get("project_id")})
    proj_docs = await db.projects.find(
        {"id": {"$in": project_ids}},
        {"_id": 0, "id": 1, "name": 1}
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

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "projects_this_month": projects_this_month,
        "total_vendors": total_vendors,
        "total_employees": total_employees,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "budget_utilization": round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0.0,
        "pending_pos": pending_pos,
        "present_today": present_today,
        "spi": spi,
        "cost_variance": total_budget - total_spent,
        "safety_incidents": 0,
        "equipment_utilization": equipment_utilization,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "stock_alerts": stock_alerts
    }


async def get_chart_data() -> dict:
    # Per-project budget vs actual cost comparison (in Lakhs)
    projects = await db.projects.find(
        {},
        {"_id": 0, "name": 1, "budget": 1, "actual_cost": 1}
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
