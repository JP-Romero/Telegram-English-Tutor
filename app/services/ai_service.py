import io
import base64
import logging
import httpx
from typing import List, Dict, Optional
from groq import Groq, APIError

from app.core.config import settings

logger = logging.getLogger("TutorApp.AIService")

SYSTEM_PROMPT = """
You are "Echo", a friendly and versatile bilingual English tutor on Telegram.
You can adapt to any role the user needs: teacher, translator, conversation partner, or study buddy.
You assist users practicing English through text, voice notes, and images.

IMPORTANT: The user is a Spanish speaker learning English. ALWAYS respond in Spanish.

ADAPTIVE ROLES:
- 🎓 MAESTRO: If the user wants to learn, teach them step by step with examples, exercises, and explanations in Spanish.
- 🔄 TRADUCTOR: If the user wants translation, translate accurately and explain nuances.
- 💬 CONVERSACIÓN: If the user wants to practice, have natural conversations and correct gently.
- 📚 EXÁMENES: If the user is studying for a test, help with practice questions and tips.

TOPICS YOU CAN HELP WITH:
🏥 Salud | 🔬 Ciencia | ✈️ Viajes | 💼 Negocios | 🎮 Hobbies | 🏫 Escuela | 💻 Tecnología | 🏨 Hotelería | 🍳 Cocina | 🎬 Entretenimiento | ⚽ Deportes | 🎵 Música | 📰 Actualidad | 🏠 Vida diaria

RULES FOR RESPONDING:
1. Always respond in Spanish.
2. Be warm, patient, and encouraging — like a supportive friend.
3. Detect what the user wants and adapt your role.
4. For TEXT inputs:
   - Correct grammar/spelling if needed:
     💡 *Corrección:* [Frase corregida en inglés]
   - Always provide the English translation and explain why:
     🇪🇸 *En español:* [Lo que significa]
     🇬🇧 *En inglés:* [La frase correcta]
5. For VOICE NOTES / AUDIO inputs:
   - The user's speech has been transcribed to text.
   - Provide feedback on pronunciation or word choice if needed:
     🎯 *Retroalimentación:* [Comentario breve sobre claridad/pronunciación]
   - Provide grammar corrections if necessary:
     💡 *Gramática:* [Frase corregida]
   - Always include the Spanish translation.
6. For IMAGE inputs:
   - Describe what you see in the image in Spanish.
   - If there's text in the image, translate it to English and explain it.
   - Help the user learn vocabulary related to the image.
   - Always include English translations and explanations.
7. End each response with a question to keep the conversation going.
8. Use simple language and emojis to make it fun and engaging.
9. Cover any topic the user asks about — be knowledgeable and helpful.
"""


class GroqTutorService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada.")
        self.client = Groq(api_key=api_key)
        self.chat_model = "openai/gpt-oss-20b"
        self.vision_model = "llama-4-scout-17b-16e-instruct"
        self.whisper_model = "whisper-large-v3-turbo"
        self.http_client = httpx.AsyncClient(timeout=30.0)

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
                max_tokens=500,
            )
            return response.choices[0].message.content or "No pude procesar tu mensaje. ¡Intenta de nuevo!"

        except APIError as e:
            logger.error(f"Error de API de Groq (Texto): {e}", exc_info=True)
            return "Estoy teniendo problemas con mi cerebro de IA. ¡Intenta de nuevo en un momento!"
        except Exception as e:
            logger.error(f"Error inesperado en GroqTutorService (Texto): {e}", exc_info=True)
            return "Ocurrió un error al procesar tu texto."

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
            return "Tuve problemas procesando tu nota de voz. ¡Intenta enviarla de nuevo!"
        except Exception as e:
            logger.error(f"Error inesperado en GroqTutorService (Audio): {e}", exc_info=True)
            return "Algo salió mal al procesar tu nota de voz."

    async def generate_tutor_image_response(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Procesa imágenes usando el modelo de visión de Groq."""
        try:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            if history:
                for msg in history:
                    role = msg["role"]
                    if role == "model":
                        role = "assistant"
                    messages.append({"role": role, "content": msg["content"]})

            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Describe esta imagen en español, traduce cualquier texto que veas al inglés, y ayuda al usuario a aprender vocabulario relacionado."
                    }
                ]
            })

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content or "No pude procesar la imagen. ¡Intenta de nuevo!"

        except APIError as e:
            logger.error(f"Error de API de Groq (Visión): {e}", exc_info=True)
            return "Tuve problemas analizando la imagen. ¡Intenta enviarla de nuevo!"
        except Exception as e:
            logger.error(f"Error inesperado en GroqTutorService (Visión): {e}", exc_info=True)
            return "Ocurrió un error al procesar la imagen."

    async def generate_image(self, prompt: str) -> Optional[str]:
        """Genera una imagen usando Pollinations.ai (gratis)."""
        try:
            url = f"https://image.pollinations.ai/prompt/{prompt}"
            response = await self.http_client.get(url, follow_redirects=True)
            if response.status_code == 200:
                return url
            return None
        except Exception as e:
            logger.error(f"Error generando imagen: {e}", exc_info=True)
            return None


ai_service = GroqTutorService(api_key=settings.GROQ_API_KEY)
