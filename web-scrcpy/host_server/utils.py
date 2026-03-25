import requests
from config import settings


def send_message_to_telegram(text: str):
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    chat_id = settings.TELEGRAM_DEVICES_CHAT_ID or settings.TELEGRAM_ALLOWED_USER_ID
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        data=data,
        timeout=5,
    )
