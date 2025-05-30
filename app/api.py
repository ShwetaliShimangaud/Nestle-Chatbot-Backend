from fastapi import APIRouter, HTTPException, Request
from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import get_chat_response

router = APIRouter()

    
@router.post("", response_model=ChatResponse)
async def chat(request_data: ChatRequest, request: Request):
    try:
        result = await get_chat_response(request_data.message, request)
        return ChatResponse(response=result)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
