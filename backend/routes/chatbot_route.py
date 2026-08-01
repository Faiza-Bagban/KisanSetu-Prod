#backend/routes/chatbot_route.py
from fastapi import APIRouter, Depends, HTTPException
from auth.role_checker import RoleChecker
from pydantic import BaseModel, Field
from modules.rag_chatbot import chatbot_answer

router = APIRouter()
allow_authenticated = RoleChecker(["admin", "farmer", "field_officer", "district_officer"])

class ChatbotRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)

@router.post("/api/chatbot", dependencies=[Depends(allow_authenticated)])
def ask_chatbot(req: ChatbotRequest):
    """
    RAG Chatbot: answers farmer questions about government schemes using
    real scheme documents + live crop-risk data. Supports English, Hindi,
    and Marathi — auto-detects language and responds natively in it.
    Requires Ollama running locally — degrades gracefully with an
    'unavailable' message if not reachable (e.g. on constrained hosting).
    """
    try:
        result = chatbot_answer(req.query)
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot Error: {str(e)}")