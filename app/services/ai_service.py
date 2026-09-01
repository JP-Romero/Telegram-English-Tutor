import logging
from typing import List, Dict, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings

logger = logging.getLogger("TutorApp.AIService")

SYSTEM_PROMPT = """
You are "Echo", a supportive and expert English tutor on Telegram.
You assist users practicing conversational English through text and voice notes.

RULES FOR RESPONDING:
1. Short & Direct: Mobile-friendly responses (2 to 4 sentences max).
2. For VOICE NOTES / AUDIO inputs:
   - Provide feedback on pronunciation or word choice if needed:
     🎯 *Speaking Feedback:* [Brief feedback on clarity/pronunciation]
   - Provide grammar corrections if necessary:
     💡 *Grammar:* [Corrected phrasing]
3. For TEXT inputs:
   - Provide grammar/spelling corrections if necessary:
     💡 *Correction:* [Corrected sentence]
4. Always maintain a warm tone and end with an engaging open-ended question.
"""


class GeminiService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY no está configurada.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-1.5-flash"

    async def generate_tutor_response(
        self,
        user_text: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Procesa entradas puramente de texto."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=350,
            )

            contents = self._build_contents_with_history(history)
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_text)],
                )
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            return response.text or "I couldn't process your message. Try again!"

        except APIError as e:
            logger.error(f"Error de API de Gemini (Texto): {e}", exc_info=True)
            return "I'm having connection issues with my AI brain. Try again shortly."
        except Exception as e:
            logger.error(
                f"Error inesperado en GeminiService (Texto): {e}", exc_info=True
            )
            return "An error occurred while processing your text."

    async def generate_tutor_voice_response(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/ogg",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Procesa notas de voz vía inferencia multimodal."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=350,
            )

            contents = self._build_contents_with_history(history)

            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            prompt_part = types.Part.from_text(
                text="Please listen to my voice note, evaluate my speaking/grammar, and reply."
            )

            contents.append(
                types.Content(role="user", parts=[audio_part, prompt_part])
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            return (
                response.text
                or "I listened to your voice note, but I couldn't generate a reply."
            )

        except APIError as e:
            logger.error(f"Error de API de Gemini (Audio): {e}", exc_info=True)
            return "I had trouble processing your audio file. Please try sending it again."
        except Exception as e:
            logger.error(
                f"Error inesperado en GeminiService (Audio): {e}", exc_info=True
            )
            return "Something went wrong while processing your voice note."

    def _build_contents_with_history(
        self, history: Optional[List[Dict[str, str]]]
    ) -> List[types.Content]:
        contents = []
        if history:
            for msg in history:
                contents.append(
                    types.Content(
                        role=msg["role"],
                        parts=[types.Part.from_text(text=msg["content"])],
                    )
                )
        return contents


ai_service = GeminiService(api_key=settings.GEMINI_API_KEY)
