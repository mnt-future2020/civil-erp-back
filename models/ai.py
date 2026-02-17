from pydantic import BaseModel
from typing import Optional, Dict


class AIRequest(BaseModel):
    query: str
    context: Optional[Dict] = None
