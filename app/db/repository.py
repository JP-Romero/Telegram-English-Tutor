import logging
from typing import List, Dict, Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("TutorApp.Repository")


class Repository:
    def __init__(self):
        try:
            self.supabase: Client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_KEY
            )
        except Exception as e:
            logger.error(f"Error al inicializar cliente de Supabase: {e}", exc_info=True)
            raise e

    async def ensure_user_exists(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: Optional[str],
    ) -> None:
        """Crea o actualiza el registro del usuario en la base de datos."""
        try:
            payload = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
            }
            # Upsert basado en telegram_id como Clave Primaria o Unique
            self.supabase.table("users").upsert(
                payload, on_conflict="telegram_id"
            ).execute()
        except Exception as e:
            logger.error(
                f"Error en ensure_user_exists para usuario {telegram_id}: {e}",
                exc_info=True,
            )

    async def get_recent_history(
        self, telegram_id: int, limit: int = 6
    ) -> List[Dict[str, str]]:
        """Recupera los últimos N mensajes para mantener la ventana de contexto."""
        try:
            response = (
                self.supabase.table("messages")
                .select("role, content")
                .eq("user_telegram_id", telegram_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            # Reordenar cronológicamente para el prompt de la IA
            messages = response.data[::-1] if response.data else []
            return [
                {"role": m["role"], "content": m["content"]} for m in messages
            ]
        except Exception as e:
            logger.error(
                f"Error recuperando historial para {telegram_id}: {e}",
                exc_info=True,
            )
            return []

    async def save_message(
        self, telegram_id: int, role: str, content: str
    ) -> None:
        """Persiste una interacción en la tabla de mensajes."""
        try:
            payload = {
                "user_telegram_id": telegram_id,
                "role": role,
                "content": content,
            }
            self.supabase.table("messages").insert(payload).execute()
        except Exception as e:
            logger.error(
                f"Error guardando mensaje para {telegram_id}: {e}", exc_info=True
            )


repo = Repository()
