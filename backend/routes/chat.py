from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.openrouter_service import chat_with_streaming, get_text_response, generate_quiz

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    context: str = ""
    voice_mode: bool = False


class QuizRequest(BaseModel):
    context: str = ""
    num_questions: int = 4


@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Chat with AI Professor (non-streaming version).
    Powered by OpenRouter API with Claude or GPT models.
    """
    try:
        response = await get_text_response(
            request.question,
            request.context,
            voice_mode=request.voice_mode
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses for real-time conversation.
    Best for voice interactions and live feedback.
    """
    try:
        response_text = ""
        async for chunk in chat_with_streaming(
            request.question,
            request.context,
            voice_mode=request.voice_mode
        ):
            response_text += chunk
        
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


@router.post("/quiz")
async def generate_quiz_endpoint(request: QuizRequest):
    """Generate multiple choice quiz questions from lecture notes."""
    try:
        questions = await generate_quiz(request.context, request.num_questions)
        if not questions:
            raise ValueError("Failed to generate valid quiz questions")
        return {"questions": questions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Could not parse quiz: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {str(e)}")
