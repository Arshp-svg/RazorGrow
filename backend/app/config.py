from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    razorpay_key_id: str = "rzp_test_placeholder"
    razorpay_key_secret: str = "rzp_secret_placeholder"
    groq_api_key: str = "gsk_placeholder"
    
    jwt_secret_key: str = "razorgrow_default_jwt_secret_key_change_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    razorpay_webhook_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()