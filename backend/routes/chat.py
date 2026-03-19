from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_service import ask_about_notes, generate_quiz

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    context: str = ""


class QuizRequest(BaseModel):
    context: str = ""
    num_questions: int = 4


@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    try:
        response = await ask_about_notes(request.question, request.context)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")


@router.post("/quiz")
async def generate_quiz_endpoint(request: QuizRequest):
    try:
        questions = await generate_quiz(request.context, request.num_questions)
        return {"questions": questions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Could not parse quiz: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {str(e)}")
