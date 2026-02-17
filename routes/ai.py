from fastapi import APIRouter, Depends
from models.ai import AIRequest
from models.hrms import Employee
from core.auth import get_current_user
from controllers import ai_controller

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/predict")
async def ai_prediction(request: AIRequest, current_user: Employee = Depends(get_current_user)):
    return await ai_controller.ai_prediction(request)
