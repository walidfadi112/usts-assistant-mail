
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "USTS Assistant Mail"

    database_url: str = (
        "sqlite:///C:/Users/ouali/assistant-mail-usts/backend/usts.db"
    )

    secret_key: str = "CHANGE_THIS_SECRET_BEFORE_DEPLOYMENT"
    access_token_expire_minutes: int = 60
    webhook_secret: str = "CHANGE_THIS_WEBHOOK_SECRET"

    # Configuration du fournisseur IA Groq
   os.getenv("GROQ_API_KEY", "")
    groq_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
