from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLog(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_role: str
    action: str          # LOGIN, LOGOUT, CREATE, UPDATE, DELETE
    module: str          # auth, procurement, inventory, projects, etc.
    resource: str        # vendor, purchase_order, grn, employee, etc.
    resource_id: Optional[str] = None
    description: str     # "Created vendor 'TMT Steels Ltd'"
    ip_address: Optional[str] = None
    timestamp: datetime
