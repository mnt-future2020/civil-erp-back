from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import uuid
from datetime import datetime, timezone

# Load config first (triggers dotenv)
from config import MODULES
from database import db, client

# Import all routers
from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.projects import router as projects_router
from routes.financial import router as financial_router
from routes.procurement import router as procurement_router
from routes.hrms import router as hrms_router
from routes.rbac import router as rbac_router
from routes.compliance import router as compliance_router
from routes.einvoice import router as einvoice_router
from routes.settings import router as settings_router
from routes.documents import router as documents_router
from routes.ai import router as ai_router
from routes.reports import router as reports_router
from routes.inventory import router as inventory_router

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="Civil Construction ERP API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers under /api prefix
API_PREFIX = "/api"
app.include_router(auth_router,        prefix=API_PREFIX)
app.include_router(dashboard_router,   prefix=API_PREFIX)
app.include_router(projects_router,    prefix=API_PREFIX)
app.include_router(financial_router,   prefix=API_PREFIX)
app.include_router(procurement_router, prefix=API_PREFIX)
app.include_router(hrms_router,        prefix=API_PREFIX)
app.include_router(rbac_router,        prefix=API_PREFIX)
app.include_router(compliance_router,  prefix=API_PREFIX)
app.include_router(einvoice_router,    prefix=API_PREFIX)
app.include_router(settings_router,    prefix=API_PREFIX)
app.include_router(documents_router,   prefix=API_PREFIX)
app.include_router(ai_router,          prefix=API_PREFIX)
app.include_router(reports_router,     prefix=API_PREFIX)
app.include_router(inventory_router,   prefix=API_PREFIX)


# ── Root / Health ──────────────────────────────────────────

@app.get("/api/")
async def root():
    return {"message": "Civil Construction ERP API", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Startup / Shutdown ─────────────────────────────────────

@app.on_event("startup")
async def seed_default_roles():
    existing = await db.roles.find_one({"name": "admin"})
    if not existing:
        all_true = {"view": True, "create": True, "edit": True, "delete": True}
        admin_role = {
            "id": str(uuid.uuid4()),
            "name": "admin",
            "label": "Administrator",
            "description": "Full system access",
            "is_system": True,
            "permissions": {m: all_true for m in MODULES},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.roles.insert_one(admin_role)
        logger.info("Default admin role seeded successfully")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
