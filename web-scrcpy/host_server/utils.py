import requests
from config import settings


def send_message_to_telegram(text: str):
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    data = {
        "chat_id": settings.TELEGRAM_ALLOWED_USER_ID,
        "text": text,
    }
    requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        data=data,
        timeout=5,
    )
