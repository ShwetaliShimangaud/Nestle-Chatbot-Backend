from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.openai_service import get_chat_response

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await get_chat_response(request.message)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
