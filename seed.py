"""
Seed script for Civil ERP - Creates demo admin user and sample data
Run: python seed.py
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


async def seed():
    print("Starting seed...")

    # ==================== ADMIN EMPLOYEE (merged users+employees) ====================
    existing = await db.employees.find_one({"email": "admin@civilcorp.com"})
    if existing:
        print("Admin employee already exists, skipping...")
    else:
        admin_id = str(uuid.uuid4())
        admin_employee = {
            "id": admin_id,
            "name": "Admin",
            "employee_code": "EMP-0001",
            "email": "admin@civilcorp.com",
            "password": pwd_context.hash("admin123"),
            "role": "admin",
            "designation": "System Administrator",
            "department": "Management",
            "phone": "9876543210",
            "date_of_joining": "2025-01-01",
            "basic_salary": 100000.0,
            "hra": 20000.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        await db.employees.insert_one(admin_employee)
        print(f"Admin employee created: admin@civilcorp.com / admin123")

    # ==================== DEMO PROJECT ====================
    existing_project = await db.projects.find_one({"code": "PROJ-001"})
    if existing_project:
        print("Demo project already exists, skipping...")
    else:
        admin_doc = await db.employees.find_one({"email": "admin@civilcorp.com"})
        project = {
            "id": str(uuid.uuid4()),
            "name": "Chennai Metro Phase 3",
            "code": "PROJ-001",
            "description": "Metro rail construction project covering 45km stretch in Chennai",
            "client_name": "CMRL",
            "location": "Chennai, Tamil Nadu",
            "start_date": "2026-01-15",
            "expected_end_date": "2028-06-30",
            "budget": 25000000.00,
            "status": "in_progress",
            "site_engineer_id": None,
            "created_by": admin_doc["id"] if admin_doc else "",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.projects.insert_one(project)
        print(f"Demo project created: {project['name']}")

    # ==================== DEMO VENDOR ====================
    existing_vendor = await db.vendors.find_one({"code": "VND-001"})
    if existing_vendor:
        print("Demo vendor already exists, skipping...")
    else:
        vendor = {
            "id": str(uuid.uuid4()),
            "name": "Tamil Nadu Steel Suppliers",
            "code": "VND-001",
            "contact_person": "Murugan S",
            "email": "murugan@tnsteel.com",
            "phone": "9876500001",
            "address": "Industrial Estate, Ambattur, Chennai",
            "gst_number": "33AABCT1234F1ZP",
            "pan_number": "AABCT1234F",
            "category": "Steel & Iron",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.vendors.insert_one(vendor)
        print(f"Demo vendor created: {vendor['name']}")

    # ==================== DEFAULT RBAC ROLES ====================
    MODULES = [
        "dashboard", "projects", "financial", "procurement",
        "hrms", "compliance", "einvoicing", "reports",
        "ai_assistant", "settings"
    ]
    all_true = {"view": True, "create": True, "edit": True, "delete": True}

    existing = await db.roles.find_one({"name": "admin"})
    if existing:
        print("Admin role already exists, skipping...")
    else:
        admin_role = {
            "id": str(uuid.uuid4()), "name": "admin", "label": "Administrator",
            "description": "Full system access", "is_system": True,
            "permissions": {m: all_true for m in MODULES},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.roles.insert_one(admin_role)
        print("Admin role created")

    print("\n--- Seed complete! ---")
    print("Login credentials:")
    print("  Admin: admin@civilcorp.com / admin123")
    print("\nNote:")
    print("  - Only admin role is created by default")
    print("  - Every employee has login credentials (users merged with employees)")
    print("  - Create custom roles and employees via HRMS module")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
