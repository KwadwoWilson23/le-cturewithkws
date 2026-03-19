"""
OpenRouter API Service for voice and real-time chat with AI models.
OpenRouter is compatible with OpenAI API.
"""

from __future__ import annotations

import os
import json
from typing import AsyncGenerator
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY environment variable is required")

# Initialize OpenRouter client (OpenAI-compatible API)
client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Model options - using OpenAI models for best compatibility
# Other popular options: "gpt-4-turbo-preview", "claude-3-opus-20240229", "mistral-large"
MODEL = "gpt-4o"

PROFESSOR_SYSTEM_PROMPT = """You are 'Professor KWS', a brilliant, engaging, and highly interactive AI professor.
Your goal is to teach and explain concepts clearly. Keep responses conversational and energetic.

Teaching style:
- Be warm, encouraging, and approachable like a real professor
- Use vivid analogies to explain difficult concepts
- Always check understanding with follow-up questions
- Explain one or two major concepts at a time, not everything at once
- Use conversational language, not formal lecturing
- Refer to yourself as the AI Professor from 'lecturewithkws'

For voice responses:
- Use ONLY plain conversational sentences
- NO bullet points, NO markdown, NO numbered lists
- Keep responses to 2-4 sentences maximum
- Speak naturally and directly to the student
- Do NOT use any formatting symbols like ** or ###"""


async def chat_with_streaming(
    question: str,
    notes_context: str = "",
    voice_mode: bool = False
) -> AsyncGenerator[str, None]:
    """
    Send a message to OpenRouter and stream the response back.
    Perfect for real-time chat and voice input/output.
    
    Args:
        question: The user's question or input
        notes_context: Optional lecture notes for context
        voice_mode: If True, response optimized for text-to-speech
    
    Yields:
        Chunks of the response text as they arrive
    """
    
    system_prompt = PROFESSOR_SYSTEM_PROMPT
    
    if voice_mode:
        system_prompt += "\n\nIMPORTANT: This response will be spoken via text-to-speech. Keep it concise and natural."
    
    context_section = (
        f"LECTURE NOTES:\n{notes_context}"
        if notes_context.strip()
        else "Note: No lecture notes provided — answering from general knowledge."
    )
    
    user_message = f"{context_section}\n\nSTUDENT: {question}"
    
    try:
        # Use streaming for real-time responses
        stream = await client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"❌ Error: {str(e)}"


async def get_text_response(
    question: str,
    notes_context: str = "",
    voice_mode: bool = False
) -> str:
    """
    Get a complete text response from OpenRouter (non-streaming).
    
    Args:
        question: The user's question
        notes_context: Optional lecture notes for context
        voice_mode: If True, response optimized for text-to-speech
    
    Returns:
        Complete response text
    """
    
    system_prompt = PROFESSOR_SYSTEM_PROMPT
    
    if voice_mode:
        system_prompt += "\n\nIMPORTANT: This response will be spoken via text-to-speech. Keep it concise and natural."
    
    context_section = (
        f"LECTURE NOTES:\n{notes_context}"
        if notes_context.strip()
        else "Note: No lecture notes provided — answering from general knowledge."
    )
    
    user_message = f"{context_section}\n\nSTUDENT: {question}"
    
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def generate_quiz(
    notes_context: str,
    num_questions: int = 4
) -> list:
    """
    Generate multiple choice quiz questions from lecture notes.
    
    Args:
        notes_context: The lecture notes to generate questions from
        num_questions: Number of questions to generate (default: 4)
    
    Returns:
        List of quiz question objects with options and correct answers
    """
    
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
    
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        raw_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        questions = json.loads(raw_text)
        return questions
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse quiz JSON: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Error generating quiz: {str(e)}")
        return []


async def generate_lecture_content(
    topic: str,
    duration_minutes: int = 10,
    complexity: str = "intermediate"
) -> str:
    """
    Generate lecture content for a given topic.
    
    Args:
        topic: The topic to lecture about
        duration_minutes: Target duration for the lecture
        complexity: "beginner", "intermediate", or "advanced"
    
    Returns:
        Lecture content as plain text
    """
    
    system_prompt = f"""You are Professor KWS preparing lecture content.
Generate a {complexity} level lecture on the given topic, suitable for a {duration_minutes}-minute session.
Make it engaging, with examples and clear explanations."""

    user_message = f"Create a {duration_minutes}-minute {complexity} lecture about: {topic}"
    
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            max_tokens=3000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"
