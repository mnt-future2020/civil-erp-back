from fastapi import APIRouter, Depends
from models.ai import AIRequest
from models.hrms import Employee
from core.auth import check_permission
from controllers import ai_controller

router = APIRouter(prefix="/ai", tags=["ai"])

##kansha
@router.post("/predict")   
async def ai_prediction(request: AIRequest, current_user: Employee = Depends(check_permission("ai_assistant", "view"))):
    return await ai_controller.ai_prediction(request)
