import logging
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.api_client import create_card, delete_pending, get_pending, save_pending
from services.gemini_client import gemini_client
from config import settings

# Сообщение считается потенциальной картой если содержит 16 цифр
# (возможно с пробелами/дефисами между группами по 4)
_RE_CARD = re.compile(r'\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}')

logger = logging.getLogger(__name__)
router = Router()


def _looks_like_card(text: str) -> bool:
    return bool(_RE_CARD.search(text))


# ── Форматирование карточки подтверждения ─────────────────────────────────────

def _fmt_card(data: dict) -> str:
    from datetime import date

    card_num = data.get("card_number") or "—"

    purchase = data.get("purchase_date")
    if purchase:
        try:
            purchase = date.fromisoformat(purchase).strftime("%d.%m.%Y")
        except ValueError:
            pass

    return (
        "📋 Проверь данные карты:\n\n"
        f"👤 ФИО: {data.get('full_name') or '—'}\n"
        f"🏦 Банк: {data.get('bank') or '—'}\n"
        f"💳 Карта: {card_num}\n"
        f"📱 Телефон: {data.get('phone_number') or '—'}"
    )


def _confirmation_keyboard(msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"card:confirm:{msg_id}"),
        InlineKeyboardButton(text="✏️ Исправить",  callback_data=f"card:edit:{msg_id}"),
        InlineKeyboardButton(text="❌ Отмена",      callback_data=f"card:cancel:{msg_id}"),
    ]])


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Отправь данные карты в любом формате, и я добавлю её в панель."
    )


# ── Основной хендлер: любой текст ─────────────────────────────────────────────

@router.message(F.text)
async def handle_text(message: Message):
    if not _looks_like_card(message.text):
        return

    if not settings.gemini_api_key:
        await message.answer("⚠️ Gemini API ключ не настроен. Укажи его в настройках панели.")
        return

    processing_msg = await message.answer("⏳ Распознаю данные карты…")

    card_data = await gemini_client.parse_card(message.text)

    if not card_data or not card_data.get("card_number"):
        await processing_msg.edit_text(
            "❌ Не удалось распознать данные карты.\n\n"
            "Пришли данные в другом формате (ФИО, номер карты, банк, телефон)."
        )
        return

    from datetime import date
    if not card_data.get("purchase_date"):
        card_data["purchase_date"] = date.today().isoformat()

    chat = message.chat
    card_data["group_name"] = chat.title or chat.full_name or chat.username or ""

    await save_pending(processing_msg.message_id, message.from_user.id, card_data)

    await processing_msg.edit_text(
        _fmt_card(card_data),
        reply_markup=_confirmation_keyboard(processing_msg.message_id),
    )


# ── Callback: подтвердить ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("card:confirm:"))
async def cb_confirm(callback: CallbackQuery):
    msg_id = int(callback.data.split(":")[-1])
    card_data = await get_pending(msg_id)
    if not card_data:
        await callback.answer("Данные устарели. Отправь карту заново.", show_alert=True)
        return

    await delete_pending(msg_id)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    try:
        payload = {k: v for k, v in card_data.items() if v is not None}
        if "phone_number" in payload and payload["phone_number"]:
            import re as _re
            digits = _re.sub(r"\D", "", payload["phone_number"])
            if len(digits) == 11 and digits[0] in ("7", "8"):
                payload["phone_number"] = "+7" + digits[1:]
            elif len(digits) != 11:
                payload.pop("phone_number", None)
        await create_card(payload)
        await callback.message.answer("✅ Карта успешно добавлена в панель!")
    except Exception as exc:
        logger.error("Ошибка при создании карты: %s", exc)
        await callback.message.answer(f"❌ Ошибка при сохранении: {exc}")


# ── Callback: исправить ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("card:edit:"))
async def cb_edit(callback: CallbackQuery):
    msg_id = int(callback.data.split(":")[-1])
    await delete_pending(msg_id)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "✏️ Хорошо. Отправь данные карты заново в любом удобном формате."
    )


# ── Callback: отмена ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("card:cancel:"))
async def cb_cancel(callback: CallbackQuery):
    msg_id = int(callback.data.split(":")[-1])
    await delete_pending(msg_id)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Отменено.")
