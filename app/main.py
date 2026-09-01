import io
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Header, HTTPException, status
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from app.core.config import settings
from app.services.ai_service import ai_service
from app.db.repository import repo

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("TutorApp")

telegram_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()


# --- HANDLERS DE TELEGRAM ---


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.from_user:
        user = update.message.from_user
        await repo.ensure_user_exists(user.id, user.username, user.first_name)

        welcome_text = (
            f"👋 **Hello {user.first_name}! I am Echo, your AI English Tutor.**\n\n"
            "You can send me **text messages** or **voice notes** 🎙️ in English.\n"
            "I'll give you feedback on your grammar and pronunciation!\n\n"
            "*Send me a voice note or message to start!*"
        )
        await update.message.reply_markdown(welcome_text)


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.message.text or not update.message.from_user:
        return

    user_text = update.message.text
    user = update.message.from_user
    logger.info(f"Texto recibido de {user.id}: {user_text}")

    await repo.ensure_user_exists(user.id, user.username, user.first_name)
    await context.bot.send_chat_action(
        chat_id=update.message.chat_id, action="typing"
    )

    history = await repo.get_recent_history(user.id, limit=6)
    ai_response = await ai_service.generate_tutor_response(user_text, history)

    await repo.save_message(user.id, "user", user_text)
    await repo.save_message(user.id, "model", ai_response)

    try:
        await update.message.reply_markdown(ai_response)
    except Exception:
        await update.message.reply_text(ai_response)


async def handle_voice_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.message.voice or not update.message.from_user:
        return

    user = update.message.from_user
    logger.info(f"Nota de voz recibida de {user.id}")

    await repo.ensure_user_exists(user.id, user.username, user.first_name)
    await context.bot.send_chat_action(
        chat_id=update.message.chat_id, action="typing"
    )

    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        out_buffer = io.BytesIO()
        await voice_file.download_to_memory(out_buffer)
        audio_bytes = out_buffer.getvalue()

        mime_type = update.message.voice.mime_type or "audio/ogg"

        history = await repo.get_recent_history(user.id, limit=6)
        ai_response = await ai_service.generate_tutor_voice_response(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            history=history,
        )

        await repo.save_message(user.id, "user", "[Voice Note Sent]")
        await repo.save_message(user.id, "model", ai_response)

        try:
            await update.message.reply_markdown(ai_response)
        except Exception:
            await update.message.reply_text(ai_response)

    except Exception as e:
        logger.error(f"Error procesando nota de voz de {user.id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I had trouble downloading or listening to your voice note."
        )


# Registrar Handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
)
telegram_app.add_handler(
    MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message)
)


# --- FASTAPI LIFESPAN & ROUTING ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicación y registrando Webhook...")
    await telegram_app.initialize()
    await telegram_app.start()

    bot: Bot = telegram_app.bot
    webhook_endpoint = f"{settings.WEBHOOK_URL.rstrip('/')}/webhook"
    try:
        await bot.set_webhook(
            url=webhook_endpoint,
            secret_token=settings.SECRET_TOKEN,
            drop_pending_updates=True,
        )
        logger.info(f"Webhook activo en: {webhook_endpoint}")
    except Exception as e:
        logger.warning(f"No se pudo registrar webhook: {e}. La app seguirá funcionando.")

    yield

    logger.info("Cerrando aplicación...")
    await bot.delete_webhook()
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}


@app.post("/webhook")
async def handle_telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    if x_telegram_bot_api_secret_token != settings.SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )

    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error procesando Webhook: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
