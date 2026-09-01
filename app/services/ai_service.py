import io
import logging
from typing import List, Dict, Optional
from groq import Groq, APIError

from app.core.config import settings

logger = logging.getLogger("TutorApp.AIService")

SYSTEM_PROMPT = """
You are "Echo", a friendly and expert bilingual English tutor on Telegram.
You assist users practicing conversational English through text and voice notes.

IMPORTANT: The user is a Spanish speaker learning English. ALWAYS respond in Spanish.

RULES FOR RESPONDING:
1. Always respond in Spanish.
2. Be warm, patient, and encouraging — like a supportive friend.
3. For TEXT inputs:
   - Correct grammar/spelling if needed:
     💡 *Corrección:* [Frase corregida en inglés]
   - Always provide the English translation and explain why:
     🇪🇸 *En español:* [Lo que significa]
     🇬🇧 *En inglés:* [La frase correcta]
4. For VOICE NOTES / AUDIO inputs:
   - The user's speech has been transcribed to text.
   - Provide feedback on pronunciation or word choice if needed:
     🎯 *Retroalimentación:* [Comentario breve sobre claridad/pronunciación]
   - Provide grammar corrections if necessary:
     💡 *Gramática:* [Frase corregida]
   - Always include the Spanish translation.
5. End each response with a question to keep the conversation going.
6. Use simple language and emojis to make it fun and engaging.
"""


class GroqTutorService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada.")
        self.client = Groq(api_key=api_key)
        self.chat_model = "openai/gpt-oss-20b"
        self.whisper_model = "whisper-large-v3-turbo"

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
                    role = msg["role"]
                    if role == "model":
                        role = "assistant"
                    messages.append({"role": role, "content": msg["content"]})

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
