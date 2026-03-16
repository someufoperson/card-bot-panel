import json
import logging
import re

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

_CARD_PROMPT = """Извлеки данные банковской карты из текста. Верни ТОЛЬКО JSON без пояснений:
{
  "full_name": "ФИО строкой или null",
  "bank": "название банка или null",
  "card_number": "только цифры без пробелов или null",
  "phone_number": "+7XXXXXXXXXX или null",
  "purchase_date": "YYYY-MM-DD или null",
  "group_name": null
}
Если данных недостаточно — верни поля как null, не придумывай."""


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    async def parse_card(self, text: str) -> dict | None:
        """Отправляет текст в Gemini, возвращает распознанные поля карты или None при ошибке."""
        try:
            response = self._model.generate_content(f"{_CARD_PROMPT}\n\nТекст:\n{text}")
            raw = response.text.strip()

            # Убираем возможные markdown-блоки ```json ... ```
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            data = json.loads(raw)
            return data
        except Exception as exc:
            logger.error("Gemini parse error: %s", exc)
            return None


gemini_client = GeminiClient()
