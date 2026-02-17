from fastapi import HTTPException
import os
import logging

from openai import AsyncOpenAI

from database import db
from models.ai import AIRequest

logger = logging.getLogger(__name__)


async def ai_prediction(request: AIRequest) -> dict:
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")

        projects = await db.projects.find({}, {"_id": 0}).to_list(10)
        context_str = f"Current projects: {len(projects)}"
        if request.context:
            context_str += f"\nAdditional context: {request.context}"

        system_message = """You are an AI assistant for a Civil Construction ERP system in Tamil Nadu, India.
You help with:
- Cost predictions and budget forecasting
- Risk analysis for construction projects
- Schedule optimization suggestions
- Material requirement predictions
- GST and RERA compliance guidance

Provide concise, actionable insights. Use INR for all monetary values.
When analyzing data, consider Indian construction industry standards and Tamil Nadu specific regulations."""

        openai_client = AsyncOpenAI(api_key=api_key)
        completion = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"{request.query}\n\nContext: {context_str}"}
            ]
        )
        response = completion.choices[0].message.content
        return {"response": response, "model": "gpt-4o"}
    except Exception as e:
        logger.error(f"AI prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
