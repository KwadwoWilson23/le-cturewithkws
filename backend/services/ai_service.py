import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL = "gemini-2.0-flash"


async def ask_about_notes(question: str, notes_context: str, voice_mode: bool = False) -> str:
    system_prompt = """You are 'Professor KWS', a brilliant, engaging, and highly interactive AI professor.
A student has uploaded their lecture notes, and your goal is to TEACH them the material, not just answer questions.

Your teaching style:
- START PROACTIVELY: If this is the beginning of a session, introduce the main topic of the uploaded notes in an exciting way.
- CONVERSATIONAL: Speak like a real human teacher. Use "I'm so glad you shared these notes" or "Let's dive into [Topic] together".
- INTERACTIVE: Always end your response with a thought-provoking follow-up question to check the student's understanding.
- NO OVERLOADING: Explain one or two major concepts at a time.
- ANALOGIES: Use vivid, relatable analogies to explain difficult technical concepts.
- BRANDING: Refer to yourself as your AI Tutor from 'lecturewithkws'.

Keep responses punchy, conversational, and energetic. Use formatting like **bold** sparingly for emphasis."""

    if voice_mode:
        system_prompt += """

IMPORTANT — VOICE MODE: Your response will be spoken aloud via text-to-speech.
- Use ONLY plain conversational sentences. NO bullet points, NO markdown, NO numbered lists, NO asterisks.
- Keep responses to 2–4 sentences maximum.
- Speak as if talking directly to the student face-to-face.
- Do NOT use any formatting symbols like ** or ### or - or 1.
"""

    context_section = (
        f"LECTURE NOTES:\n{notes_context}"
        if notes_context.strip()
        else "Note: No lecture notes uploaded yet — answering from general knowledge."
    )

    user_message = f"{context_section}\n\nSTUDENT QUESTION: {question}"

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=user_message,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": 1024,
        },
    )

    return response.text


async def generate_quiz(notes_context: str, num_questions: int = 4) -> list:
    system_prompt = """You are an expert education assessment specialist.
Generate multiple choice quiz questions based on the provided lecture notes.

Return ONLY valid JSON — an array of question objects. Each object must have:
- id: integer
- question: string
- options: array of 4 strings
- correct: integer (0-indexed position of correct answer)
- explanation: string (why the correct answer is right)

Do not include any text outside the JSON array. Do not wrap in markdown code blocks."""

    user_message = f"Generate {num_questions} multiple choice questions from these lecture notes:\n\n{notes_context[:4000]}"

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=user_message,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": 2048,
        },
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    questions = json.loads(raw)
    return questions