import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), '../../.env'),
        extra="ignore",
    )


class Setting(Settings):
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ALLOWED_USER_ID: int = 0
    TELEGRAM_DEVICES_CHAT_ID: str = ""


settings = Setting()
