from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
import uuid
from datetime import datetime, timezone


class ModulePermissions(BaseModel):
    view: bool = False
    create: bool = False
    edit: bool = False
    delete: bool = False


class RoleCreate(BaseModel):
    name: str
    label: str
    description: Optional[str] = None
    permissions: Dict[str, ModulePermissions]


class RoleUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, ModulePermissions]] = None


class Role(RoleCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_system: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
