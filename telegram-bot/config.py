from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: str
    telegram_allowed_user_id: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # URL FastAPI внутри Docker-сети
    fastapi_url: str = "http://backend:8000"


settings = Settings()
