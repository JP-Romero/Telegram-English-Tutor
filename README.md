# Telegram English Tutor AI 🎙️🤖

Bot de Telegram impulsado por FastAPI, Google Gemini 2.5 Flash y Supabase para practicar conversación en inglés mediante texto y notas de voz.

## Características
- Inferencia multimodal directa (audio a texto y retroalimentación sin pasos intermedios de STT).
- Persistencia de historial conversacional en Supabase PostgreSQL.
- Autenticación de Webhooks con Token Secreto.
- Containerización Docker optimizada para capas gratuitas (Render / Koyeb).

## Instalación y Uso Local

1. Clona el repositorio e instala dependencias:
   ```bash
   cp .env.example .env
   # Configura tus variables en .env
   ```
