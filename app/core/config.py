import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Telegram English Tutor AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: str
    SECRET_TOKEN: str

    GEMINI_API_KEY: str

    SUPABASE_URL: str
    SUPABASE_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
