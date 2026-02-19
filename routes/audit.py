from fastapi import APIRouter, Depends, Query, HTTPException
from core.auth import get_current_user
from models.hrms import Employee
from controllers import audit_controller

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    module: str = Query(None),
    action: str = Query(None),
    user_id: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search: str = Query(None),
    current_user: Employee = Depends(get_current_user),
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await audit_controller.get_audit_logs(
        page=page, limit=limit, module=module, action=action,
        user_id=user_id, date_from=date_from, date_to=date_to, search=search,
    )
