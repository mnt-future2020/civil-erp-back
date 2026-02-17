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

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    present_today = await db.attendance.count_documents({"date": today, "status": "present"})

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_vendors": total_vendors,
        "total_employees": total_employees,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "budget_utilization": (total_spent / total_budget * 100) if total_budget > 0 else 0,
        "pending_pos": pending_pos,
        "present_today": present_today,
        "spi": 0.97,
        "cost_variance": total_budget - total_spent,
        "safety_incidents": 0,
        "equipment_utilization": 87.5
    }


async def get_chart_data() -> dict:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    budget_data = [120, 150, 180, 200, 220, 250]
    actual_data = [115, 155, 170, 210, 215, 240]

    return {
        "monthly_cost": {
            "labels": months,
            "budget": budget_data,
            "actual": actual_data
        },
        "project_status": {
            "planning": await db.projects.count_documents({"status": "planning"}),
            "in_progress": await db.projects.count_documents({"status": "in_progress"}),
            "on_hold": await db.projects.count_documents({"status": "on_hold"}),
            "completed": await db.projects.count_documents({"status": "completed"})
        },
        "expense_breakdown": {
            "materials": 45,
            "labor": 30,
            "equipment": 15,
            "overhead": 10
        }
    }
