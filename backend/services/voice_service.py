"""
Voice Service for handling audio input/output with text-to-speech and speech-to-text.
Integrates with OpenRouter for AI responses and can use external TTS/STT APIs.
"""

from __future__ import annotations

import os
import io
import base64
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class VoiceProcessor:
    """Handle voice input/output processing for real-time communication."""
    
    def __init__(self):
        self.tts_provider = os.getenv("TTS_PROVIDER", "google")  # google, elevenlabs, openai
        self.stt_provider = os.getenv("STT_PROVIDER", "google")  # google, openai
        self.sample_rate = 16000
        self.channels = 1
        self.bit_depth = 16
    
    async def text_to_speech(
        self, 
        text: str,
        voice: str = "en-US-Neural2-C",
        speed: float = 1.0
    ) -> bytes:
        """
        Convert text to speech audio bytes.
        
        Args:
            text: The text to convert to speech
            voice: Voice identifier (varies by provider)
            speed: Speech speed multiplier (0.25 to 4.0)
        
        Returns:
            Audio bytes in WAV format
        """
        
        if self.tts_provider == "google":
            return await self._google_tts(text, voice, speed)
        elif self.tts_provider == "elevenlabs":
            return await self._elevenlabs_tts(text, voice, speed)
        elif self.tts_provider == "openai":
            return await self._openai_tts(text, voice, speed)
        else:
            raise ValueError(f"Unknown TTS provider: {self.tts_provider}")
    
    async def speech_to_text(
        self,
        audio_bytes: bytes,
        language: str = "en-US"
    ) -> str:
        """
        Convert speech audio to text.
        
        Args:
            audio_bytes: Audio data in WAV or PCM format
            language: Language code (e.g., 'en-US')
        
        Returns:
            Transcribed text
        """
        
        if self.stt_provider == "google":
            return await self._google_stt(audio_bytes, language)
        elif self.stt_provider == "openai":
            return await self._openai_stt(audio_bytes, language)
        else:
            raise ValueError(f"Unknown STT provider: {self.stt_provider}")
    
    # Google Cloud Text-to-Speech
    async def _google_tts(
        self, 
        text: str,
        voice: str,
        speed: float
    ) -> bytes:
        """Google Cloud TTS implementation."""
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise ImportError("google-cloud-texttospeech is required for Google TTS")
        
        try:
            client = texttospeech.TextToSpeechClient()
            
            input_text = texttospeech.SynthesisInput(text=text)
            
            voice_config = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice,
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=speed
            )
            
            response = client.synthesize_speech(
                input=input_text,
                voice=voice_config,
                audio_config=audio_config
            )
            
            return response.audio_content
        except Exception as e:
            print(f"❌ Google TTS error: {str(e)}")
            raise
    
    # ElevenLabs Text-to-Speech
    async def _elevenlabs_tts(
        self,
        text: str,
        voice: str,
        speed: float
    ) -> bytes:
        """ElevenLabs TTS implementation for high-quality voices."""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required for ElevenLabs TTS")
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("❌ ELEVENLABS_API_KEY environment variable is required")
        
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"❌ ElevenLabs TTS error: {str(e)}")
            raise
    
    # OpenAI Text-to-Speech
    async def _openai_tts(
        self,
        text: str,
        voice: str,
        speed: float
    ) -> bytes:
        """OpenAI TTS implementation."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai is required for OpenAI TTS")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY environment variable is required")
        
        try:
            client = AsyncOpenAI(api_key=api_key)
            
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed
            )
            
            return response.content
        except Exception as e:
            print(f"❌ OpenAI TTS error: {str(e)}")
            raise
    
    # Google Cloud Speech-to-Text
    async def _google_stt(
        self,
        audio_bytes: bytes,
        language: str
    ) -> str:
        """Google Cloud STT implementation."""
        try:
            from google.cloud import speech
        except ImportError:
            raise ImportError("google-cloud-speech is required for Google STT")
        
        try:
            client = speech.SpeechClient()
            
            audio = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.sample_rate,
                language_code=language,
            )
            
            response = client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                if result.alternatives:
                    transcript += result.alternatives[0].transcript + " "
            
            return transcript.strip()
        except Exception as e:
            print(f"❌ Google STT error: {str(e)}")
            raise
    
    # OpenAI Speech-to-Text
    async def _openai_stt(
        self,
        audio_bytes: bytes,
        language: str
    ) -> str:
        """OpenAI Whisper STT implementation."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai is required for OpenAI STT")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY environment variable is required")
        
        try:
            client = AsyncOpenAI(api_key=api_key)
            
            # Convert bytes to file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
            
            return transcript.text
        except Exception as e:
            print(f"❌ OpenAI STT error: {str(e)}")
            raise
    
    @staticmethod
    def audio_to_base64(audio_bytes: bytes) -> str:
        """Convert audio bytes to base64 string for transmission."""
        return base64.b64encode(audio_bytes).decode()
    
    @staticmethod
    def base64_to_audio(audio_base64: str) -> bytes:
        """Convert base64 string back to audio bytes."""
        return base64.b64decode(audio_base64)
    
    @staticmethod
    async def trim_silence(
        audio_bytes: bytes,
        silence_threshold: float = 0.01
    ) -> bytes:
        """
        Trim leading and trailing silence from audio.
        
        Args:
            audio_bytes: Raw PCM audio bytes
            silence_threshold: Volume threshold (0.0-1.0)
        
        Returns:
            Trimmed audio bytes
        """
        try:
            import numpy as np
        except ImportError:
            print("⚠️ numpy not available, returning audio as-is")
            return audio_bytes
        
        try:
            # Convert bytes to numpy array
            audio = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Normalize to 0-1 range
            audio_normalized = np.abs(audio.astype(np.float32)) / 32768.0
            
            # Find non-silent regions
            loud_indices = np.where(audio_normalized > silence_threshold)[0]
            
            if len(loud_indices) == 0:
                return audio_bytes  # All silent
            
            start_idx = loud_indices[0]
            end_idx = loud_indices[-1]
            
            trimmed = audio[start_idx:end_idx + 1]
            return trimmed.astype(np.int16).tobytes()
        except Exception as e:
            print(f"⚠️ Error trimming silence: {str(e)}")
            return audio_bytes


# Global voice processor instance
voice_processor = VoiceProcessor()
