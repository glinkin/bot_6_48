"""Configuration settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram Bot
    telegram_bot_token: str
    
    # External Lottery API
    api_base_url: str
    api_key: str
    
    # Database
    database_url: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
