"""
AgentPay AI — Application Configuration

Loads settings from environment variables with safe defaults for development.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AgentPay AI"
    secret_key: str = "dev-secret-change-in-production"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./agentpay.db"

    # AI Provider
    ai_provider: str = "openai"  # openai | gemini
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-pro"

    # Razorpay Test Mode
    razorpay_key_id: Optional[str] = None
    razorpay_key_secret: Optional[str] = None
    razorpay_webhook_secret: Optional[str] = None

    # Demo Mode
    demo_mode: bool = True

    # Frontend
    frontend_url: str = "http://localhost:3000"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def ai_configured(self) -> bool:
        if self.ai_provider == "openai":
            return bool(self.openai_api_key)
        elif self.ai_provider == "gemini":
            return bool(self.google_api_key)
        return False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
