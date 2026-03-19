"""
Voice routes for speech-to-text and text-to-speech functionality.
Handles real-time voice communication with the AI professor.
"""

from __future__ import annotations

import base64
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from services.voice_service import voice_processor
from services.openrouter_service import get_text_response

router = APIRouter()


class VoiceToTextRequest(BaseModel):
    """Request for converting speech audio to text."""
    audio_base64: str  # Base64 encoded audio
    language: str = "en-US"


class TextToVoiceRequest(BaseModel):
    """Request for converting text to speech audio."""
    text: str
    voice: str = "en-US-Neural2-C"  # Google voice ID
    speed: float = 1.0


class VoiceChatRequest(BaseModel):
    """Request for voice chat (STT -> AI -> TTS pipeline)."""
    audio_base64: str
    context: str = ""
    language: str = "en-US"
    voice: str = "en-US-Neural2-C"
    speed: float = 1.0


@router.post("/voice/transcribe")
async def transcribe_speech(request: VoiceToTextRequest):
    """
    Convert speech audio to text using STT service.
    
    Args:
        audio_base64: Base64 encoded audio data
        language: Language code (e.g., 'en-US')
    
    Returns:
        Transcribed text
    """
    try:
        # Decode audio from base64
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Transcribe speech
        text = await voice_processor.speech_to_text(audio_bytes, request.language)
        
        return {
            "text": text,
            "language": request.language,
            "confidence": 0.95  # Placeholder - actual value depends on STT provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")


@router.post("/voice/synthesize")
async def synthesize_speech(request: TextToVoiceRequest):
    """
    Convert text to speech audio.
    
    Args:
        text: Text to convert to speech
        voice: Voice identifier
        speed: Speech speed (0.25 to 4.0)
    
    Returns:
        Base64 encoded audio data
    """
    try:
        # Validate inputs
        if not request.text:
            raise ValueError("Text cannot be empty")
        if not (0.25 <= request.speed <= 4.0):
            raise ValueError("Speed must be between 0.25 and 4.0")
        
        # Generate speech
        audio_bytes = await voice_processor.text_to_speech(
            request.text,
            request.voice,
            request.speed
        )
        
        # Encode to base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        return {
            "audio_base64": audio_base64,
            "duration_seconds": len(audio_bytes) / (16000 * 2),  # Estimate based on sample rate and bit depth
            "voice": request.voice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis error: {str(e)}")


@router.post("/voice/chat")
async def voice_chat(request: VoiceChatRequest):
    """
    Full voice interaction: Speech -> AI Response -> Speech
    
    Pipeline:
    1. Transcribe user's speech to text (STT)
    2. Get AI response using OpenRouter
    3. Convert response to speech (TTS)
    
    Args:
        audio_base64: User's voice input (base64 encoded)
        context: Optional lecture notes context
        language: Language code for recognition
        voice: Voice for TTS response
        speed: Speech speed for response
    
    Returns:
        response_text: AI's text response
        audio_base64: AI's speech response (base64 encoded)
    """
    try:
        # Step 1: Transcribe user's speech
        audio_bytes = base64.b64decode(request.audio_base64)
        user_text = await voice_processor.speech_to_text(audio_bytes, request.language)
        
        if not user_text.strip():
            raise ValueError("Could not transcribe audio - please speak clearly")
        
        # Step 2: Get AI response (voice-optimized)
        ai_response = await get_text_response(
            user_text,
            request.context,
            voice_mode=True
        )
        
        # Step 3: Synthesize response speech
        response_audio_bytes = await voice_processor.text_to_speech(
            ai_response,
            request.voice,
            request.speed
        )
        
        # Encode response to base64
        response_audio_base64 = base64.b64encode(response_audio_bytes).decode()
        
        return {
            "user_transcript": user_text,
            "response_text": ai_response,
            "audio_base64": response_audio_base64,
            "duration_seconds": len(response_audio_bytes) / (16000 * 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat error: {str(e)}")


@router.post("/voice/upload-analyze")
async def upload_and_analyze_voice(
    file: UploadFile = File(...),
    context: str = "",
    language: str = "en-US",
    voice: str = "en-US-Neural2-C"
):
    """
    Upload an audio file, transcribe it, get AI response, and return speech.
    
    Args:
        file: Audio file upload
        context: Optional lecture notes
        language: Language code
        voice: Voice for response
    
    Returns:
        Full voice chat response with transcription
    """
    try:
        # Read uploaded file
        audio_bytes = await file.read()
        
        # Transcribe
        user_text = await voice_processor.speech_to_text(audio_bytes, language)
        
        # Get AI response
        ai_response = await get_text_response(
            user_text,
            context,
            voice_mode=True
        )
        
        # Synthesize response
        response_audio_bytes = await voice_processor.text_to_speech(
            ai_response,
            voice,
            1.0
        )
        
        response_audio_base64 = base64.b64encode(response_audio_bytes).decode()
        
        return {
            "filename": file.filename,
            "user_transcript": user_text,
            "response_text": ai_response,
            "audio_base64": response_audio_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File analysis error: {str(e)}")


@router.get("/voice/config")
async def get_voice_config():
    """Get current voice configuration and available options."""
    return {
        "tts_provider": voice_processor.tts_provider,
        "stt_provider": voice_processor.stt_provider,
        "sample_rate": voice_processor.sample_rate,
        "channels": voice_processor.channels,
        "bit_depth": voice_processor.bit_depth,
        "available_voices": {
            "google": [
                "en-US-Neural2-A",
                "en-US-Neural2-C",
                "en-US-Neural2-E",
                "en-US-Neural2-F"
            ],
            "elevenlabs": [
                "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "EZvs7bWrR60B9xRmUtestified",  # Premislaus
            ]
        },
        "languages": {
            "en-US": "English (United States)",
            "en-GB": "English (United Kingdom)",
            "es-ES": "Spanish",
            "fr-FR": "French",
            "de-DE": "German",
            "zh-CN": "Chinese (Simplified)"
        }
    }
