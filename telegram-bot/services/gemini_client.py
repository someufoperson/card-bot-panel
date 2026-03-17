import json
import logging
import re

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

_CARD_PROMPT = """Ты — парсер данных банковских карт. Извлеки поля из произвольного текста на русском или английском языке — он может быть в любом формате: список, таблица, свободный текст, сокращения, опечатки.

Верни ТОЛЬКО валидный JSON без пояснений и без markdown:
{
  "full_name": "ФИО владельца строкой или null",
  "bank": "официальное название банка или null",
  "card_number": "только 16 цифр без пробелов или null",
  "phone_number": "+7XXXXXXXXXX или null",
  "purchase_date": "YYYY-MM-DD или null",
  "group_name": "группа или null"
}

━━━ ПРАВИЛА ━━━

НОРМАЛИЗАЦИЯ БАНКОВ — приводи к официальному названию:
  Сбербанк / Сбер / СБ → "Сбер"
  Тинькофф / Тинёк / Тинёф / Тинкофф / T-Bank → "Т-Банк"
  ТКБ / Транскапиталбанк / Транскапитал → "ТКБ"
  ВТБ → "ВТБ"
  Альфа / Альфа-Банк → "Альфа-Банк"
  Газпром / Газпромбанк / ГПБ → "Газпромбанк"
  Открытие → "Открытие"
  Райф / Райффайзен / Raiffeisen → "Райффайзен"
  МКБ / Московский кредитный → "МКБ"
  Совком / Совкомбанк → "Совкомбанк"
  Почта / Почта Банк → "Почта Банк"
  Росбанк → "Росбанк"
  ОТП / OTP → "ОТП Банк"
  УБРиР → "УБРиР"
  Уралсиб → "Уралсиб"
  РСХБ / Россельхозбанк → "Россельхозбанк"
  ПСБ / Промсвязьбанк → "ПСБ"
  Хоум / Home Credit → "Хоум Кредит"
  Ренессанс → "Ренессанс Банк"
  МТС / МТС Банк → "МТС Банк"
  Экспобанк → "Экспобанк"
  Если банк не из списка — напиши как есть с заглавной буквы.

ТЕЛЕФОН — приводи к формату +7XXXXXXXXXX:
  8XXXXXXXXXX → +7XXXXXXXXXX
  7XXXXXXXXXX → +7XXXXXXXXXX
  Если цифр не 11 — null.

НОМЕР КАРТЫ — ровно 16 цифр, убери пробелы/тире. Если не 16 — null.

ДАТА ПОКУПКИ — форматы ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, YYYY-MM-DD → приводи к YYYY-MM-DD. Если не указана — null.

НЕ ПРИДУМЫВАЙ данные. Поле не нашёл — строго null.

━━━━━━━━━━━━━━"""


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    async def parse_card(self, text: str) -> dict | None:
        """Отправляет текст в Gemini, возвращает распознанные поля карты или None при ошибке."""
        try:
            response = self._model.generate_content(
                f"{_CARD_PROMPT}\n\nТекст для парсинга:\n{text}"
            )
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
