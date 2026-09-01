import io
import logging
from typing import List, Dict, Optional
from groq import Groq, APIError

from app.core.config import settings

logger = logging.getLogger("TutorApp.AIService")

SYSTEM_PROMPT = """
You are "Echo", a supportive and expert English tutor on Telegram.
You assist users practicing conversational English through text and voice notes.

RULES FOR RESPONDING:
1. Short & Direct: Mobile-friendly responses (2 to 4 sentences max).
2. For VOICE NOTES / AUDIO inputs:
   - The user's speech has been transcribed to text.
   - Provide feedback on pronunciation or word choice if needed:
     🎯 *Speaking Feedback:* [Brief feedback on clarity/pronunciation]
   - Provide grammar corrections if necessary:
     💡 *Grammar:* [Corrected phrasing]
3. For TEXT inputs:
   - Provide grammar/spelling corrections if necessary:
     💡 *Correction:* [Corrected sentence]
4. Always maintain a warm tone and end with an engaging open-ended question.
"""


class GroqTutorService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada.")
        self.client = Groq(api_key=api_key)
        self.chat_model = "llama-3.3-70b-versatile"
        self.whisper_model = "whisper-large-v3"

    async def generate_tutor_response(
        self,
        user_text: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Procesa entradas puramente de texto."""
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            if history:
                for msg in history:
                    messages.append({"role": msg["role"], "content": msg["content"]})

            messages.append({"role": "user", "content": user_text})

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.7,
                max_tokens=350,
            )
            return response.choices[0].message.content or "I couldn't process your message. Try again!"

        except APIError as e:
            logger.error(f"Error de API de Groq (Texto): {e}", exc_info=True)
            return "I'm having connection issues with my AI brain. Try again shortly."
        except Exception as e:
            logger.error(f"Error inesperado en GroqTutorService (Texto): {e}", exc_info=True)
            return "An error occurred while processing your text."

    async def generate_tutor_voice_response(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/ogg",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Transcribe audio con Whisper y responde con Llama."""
        try:
            transcript = self.client.audio.transcriptions.create(
                file=("audio.ogg", io.BytesIO(audio_bytes), mime_type),
                model=self.whisper_model,
                language="en",
            )
            user_text = transcript.text
            logger.info(f"Transcripción: {user_text}")

            return await self.generate_tutor_response(user_text, history)

        except APIError as e:
            logger.error(f"Error de API de Groq (Audio): {e}", exc_info=True)
            return "I had trouble processing your audio file. Please try sending it again."
        except Exception as e:
            logger.error(f"Error inesperado en GroqTutorService (Audio): {e}", exc_info=True)
            return "Something went wrong while processing your voice note."


ai_service = GroqTutorService(api_key=settings.GROQ_API_KEY)
