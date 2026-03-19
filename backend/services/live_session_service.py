from __future__ import annotations

import os
import json
import asyncio
import uuid
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

LIVE_MODEL = "gemini-2.0-flash-exp"
PLAN_MODEL = "gemini-2.0-flash"

PROFESSOR_SYSTEM_PROMPT = """You are 'Professor KWS', a brilliant, engaging, and highly interactive AI professor delivering a LIVE lecture session.

Your teaching style:
- LECTURE MODE: You are giving a real-time spoken lecture. Teach as if you're standing in front of a classroom.
- CONVERSATIONAL: Use natural, energetic speech. Say things like "Now here's where it gets really interesting..." or "Pay close attention to this part..."
- PACING: Teach one concept at a time within the current segment. Don't rush through everything.
- ANALOGIES: Use vivid, relatable analogies to explain difficult concepts.
- ENGAGING: Ask rhetorical questions, use dramatic pauses, build excitement.
- CLEAR: Speak in plain conversational sentences. No bullet points, no markdown, no numbered lists.
- BRANDING: You are the AI Professor from 'lecturewithkws'.

When a student asks a question (voice or text), answer it clearly and concisely in context of the current lecture segment, then smoothly transition back to teaching.

Keep each teaching segment to about 2-3 minutes of natural speech."""


async def create_lecture_plan(notes_context: str) -> list:
    system_prompt = """You are a curriculum planning assistant. Given lecture notes, break them into 4-6 logical teaching segments.

Return ONLY valid JSON — an array of segment objects. Each object must have:
- segment_number: integer (starting from 1)
- title: string (short descriptive title)
- key_points: array of 2-3 strings (main concepts to cover)
- teaching_notes: string (brief guidance on how to teach this segment)

Do not include any text outside the JSON array. Do not wrap in markdown code blocks."""

    user_message = f"Break these lecture notes into teaching segments:\n\n{notes_context[:6000]}"  # type: ignore

    response = await client.aio.models.generate_content(
        model=PLAN_MODEL,
        contents=user_message,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": 2048,
        },
    )

    raw = response.text.strip()
    if "```" in raw:
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
        else:
            raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        segments = json.loads(raw)
        return segments
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse lecture plan JSON: {str(e)}")
        print(f"Raw response: {raw}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error parsing lecture plan: {str(e)}")
        return []


import typing

class LiveSessionManager:
    def __init__(self, session_id: str, notes_context: str, segments: list):
        self.session_id = session_id
        self.notes_context = notes_context
        self.segments = segments
        self.current_segment = 0
        self.gemini_session: typing.Any = None
        self._receive_task: typing.Any = None
        self._audio_callback: typing.Any = None
        self._text_callback: typing.Any = None
        self._segment_done_callback: typing.Any = None
        self._is_active = False

    async def connect(self, audio_callback: typing.Any, text_callback: typing.Any, segment_done_callback: typing.Any):
        self._audio_callback = audio_callback
        self._text_callback = text_callback
        self._segment_done_callback = segment_done_callback

        segment_overview = "\n".join(
            f"Segment {s['segment_number']}: {s['title']}"
            for s in self.segments
        )

        notes = self.notes_context[:5000]  # type: ignore
        system_instruction = f"""{PROFESSOR_SYSTEM_PROMPT}

LECTURE NOTES:
{notes}

LECTURE PLAN:
{segment_overview}

You will be told which segment to teach. Focus only on that segment's content from the notes above."""

        config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": system_instruction,
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Kore"
                    }
                }
            }
        }

        self.gemini_session = await client.aio.live.connect(
            model=LIVE_MODEL,
            config=config,
        )
        self._is_active = True
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def start_segment(self, segment_index: int):
        if not self.gemini_session or segment_index >= len(self.segments):
            return False

        self.current_segment = segment_index
        segment = self.segments[segment_index]

        prompt = (
            f"Now teach Segment {segment['segment_number']}: {segment['title']}. "
            f"Key points to cover: {', '.join(segment['key_points'])}. "
            f"Teaching guidance: {segment['teaching_notes']}. "
            f"Begin your lecture for this segment now. Speak naturally and engagingly."
        )

        await self.gemini_session.send_client_content(
            turns=types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        )
        return True

    async def _receive_loop(self):
        try:
            async for response in self.gemini_session.receive():
                if not self._is_active:
                    break

                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.inline_data and self._audio_callback:
                            await self._audio_callback(part.inline_data.data)
                        elif part.text and self._text_callback:
                            await self._text_callback(part.text)

                if response.server_content and response.server_content.turn_complete:
                    if self._segment_done_callback:
                        await self._segment_done_callback(self.current_segment)

        except Exception as e:
            if self._text_callback:
                print(f"DEBUG: Receiver error: {str(e)}")
                if self._is_active:
                    await self._text_callback(f"[Session status: {str(e)}]")

    async def send_voice_input(self, pcm_bytes: bytes):
        if not self.gemini_session:
            return

        await self.gemini_session.send_realtime_input(
            audio=types.Blob(
                data=pcm_bytes,
                mime_type="audio/pcm;rate=16000",
            )
        )

    async def send_text_question(self, text: str) -> None:
        if not self.gemini_session:
            return

        prompt = (
            f"A student just asked this question during your lecture: \"{text}\". "
            f"Answer it briefly and clearly, then say you'll continue the lecture "
            f"when they're ready."
        )

        await self.gemini_session.send_client_content(
            turns=types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        )

    async def close(self):
        self._is_active = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        if self.gemini_session:
            try:
                await self.gemini_session.close()
            except Exception:
                pass
            self.gemini_session = None


active_sessions: dict[str, LiveSessionManager] = {}


def create_session(notes_context: str, segments: list) -> str:
    session_id = str(uuid.uuid4())
    manager = LiveSessionManager(session_id, notes_context, segments)
    active_sessions[session_id] = manager
    return session_id


def get_session(session_id: str) -> LiveSessionManager | None:
    return active_sessions.get(session_id)


def remove_session(session_id: str):
    active_sessions.pop(session_id, None)
