from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str

    postgres_db: str = "cardpanel"
    postgres_user: str = "carduser"
    postgres_password: str = "changeme"

    telegram_bot_token: str = ""
    telegram_allowed_user_id: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    transactions_chat_id: str = ""

    adb_notification_interval: int = 30
    bank_package_names: str = '["com.sberbank.android","kz.homebank"]'


settings = Settings()
