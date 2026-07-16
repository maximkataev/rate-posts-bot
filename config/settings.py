"""Configuration settings loaded from Doppler."""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from doppler_sdk import DopplerSDK
    HAS_DOPPLER_SDK = True
except ImportError:
    HAS_DOPPLER_SDK = False


class Settings(BaseSettings):
    """Application settings from Doppler."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Telegram
    telegram_bot_token: str
    # Канал, посты которого оцениваем: @brutalcomrade («Неуспешный канал»)
    telegram_channel_id: int = -1001243433885

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-5.4"
    
    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5"

    # Google Gemini
    google_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"

    # DeepSeek (OpenAI-совместимый API; бот работает и без ключа — просто пропускает DeepSeek)
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    
    # OpenRouter (альтернатива для доступа к разным моделям)
    openrouter_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_doppler(cls, doppler_token: Optional[str] = None) -> "Settings":
        """
        Load settings from Doppler.

        Works with both:
        - Doppler CLI (doppler run -- python main.py) - recommended
        - Doppler SDK (programmatic access via API)
        - .env file fallback
        """
        # If using Doppler CLI, environment variables are already set
        # Just load them via pydantic
        if os.getenv("DOPPLER_PROJECT") and os.getenv("DOPPLER_CONFIG"):
            # Doppler CLI is being used
            return cls()

        # Try Doppler SDK if available and token is provided
        token = doppler_token or os.getenv("DOPPLER_TOKEN")
        if token and HAS_DOPPLER_SDK:
            try:
                doppler = DopplerSDK()
                doppler.set_access_token(token)

                secrets = doppler.secrets.list(
                    project=os.getenv("DOPPLER_PROJECT", "telegram-bot"),
                    config=os.getenv("DOPPLER_CONFIG", "prd")
                )

                # Convert Doppler secrets to dict
                env_vars = {
                    secret["name"].lower(): secret["computed"]
                    for secret in secrets.get("secrets", {}).values()
                }

                return cls(**env_vars)
            except Exception as e:
                print(f"Failed to load from Doppler SDK: {e}")
                print("Falling back to .env file...")

        # Fallback to .env file
        return cls()


# Global settings instance
settings = Settings.from_doppler()
