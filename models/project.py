from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime, timezone


class ProjectStatus:
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class ProjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    client_name: str
    location: str
    start_date: str
    expected_end_date: str
    budget: float
    site_engineer_id: Optional[str] = None


class Project(ProjectCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = ProjectStatus.PLANNING
    actual_cost: float = 0.0
    progress_percentage: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None


class ProjectStatusUpdate(BaseModel):
    status: str


class ProjectProgressUpdate(BaseModel):
    progress_percentage: float
    actual_cost: Optional[float] = None


class TaskCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    parent_task_id: Optional[str] = None
    start_date: str
    end_date: str
    estimated_cost: float = 0.0
    assigned_to: Optional[str] = None


class Task(TaskCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
    actual_cost: float = 0.0
    progress: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TaskStatusUpdate(BaseModel):
    status: str
    progress: Optional[float] = None


class DPRCreate(BaseModel):
    project_id: str
    date: str
    weather: Optional[str] = None
    # Legacy fields (kept for backward compat)
    labor_count: int = 0
    labor_entries: List[dict] = Field(default_factory=list)
    work_done: str = ""
    materials_used: Optional[str] = None
    materials_used_entries: List[dict] = Field(default_factory=list)
    issues: Optional[str] = None
    notes: Optional[str] = None
    sqft_completed: Optional[float] = None
    tomorrow_schedule: Optional[str] = None
    # Work Summary (structured)
    work_summary_entries: List[dict] = Field(default_factory=list)
    # Labour Details (extended with contractor support)
    labour_entries: List[dict] = Field(default_factory=list)
    # Material Inventory (stock tracking)
    material_stock_entries: List[dict] = Field(default_factory=list)
    # Equipment Used
    equipment_entries: List[dict] = Field(default_factory=list)
    # Next Day Requirement
    next_day_material_requests: List[dict] = Field(default_factory=list)
    next_day_equipment_requests: List[dict] = Field(default_factory=list)
    # Contractor Work Summary
    contractor_work_entries: List[dict] = Field(default_factory=list)
    # Image Upload (document IDs)
    document_ids: List[str] = Field(default_factory=list)


class DPR(DPRCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
