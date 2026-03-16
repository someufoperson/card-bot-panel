import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.api_client import create_card, get_setting
from services.gemini_client import gemini_client
from config import settings

logger = logging.getLogger(__name__)
router = Router()

# Хранилище: user_id → распознанные данные карты
_pending: dict[int, dict] = {}


# ── Авторизация ──────────────────────────────────────────────────────────────

async def _get_allowed_id() -> str:
    """Получает allowed_user_id из настроек панели, fallback — env."""
    from_api = await get_setting("allowed_user_id")
    return (from_api or settings.telegram_allowed_user_id).strip()


async def _is_allowed(user_id: int) -> bool:
    allowed = await _get_allowed_id()
    return not allowed or str(user_id) == allowed


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
        f"📱 Телефон: {data.get('phone_number') or '—'}\n"
        f"📅 Дата покупки: {purchase or '—'}\n"
        f"🗂 Группа: {data.get('group_name') or 'не указана'}"
    )


def _confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="card:confirm"),
        InlineKeyboardButton(text="✏️ Исправить",  callback_data="card:edit"),
        InlineKeyboardButton(text="❌ Отмена",      callback_data="card:cancel"),
    ]])


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message):
    if not await _is_allowed(message.from_user.id):
        return
    await message.answer(
        "👋 Привет! Отправь данные карты в любом формате, и я добавлю её в панель."
    )


# ── Основной хендлер: любой текст ─────────────────────────────────────────────

@router.message(F.text)
async def handle_text(message: Message):
    if not await _is_allowed(message.from_user.id):
        logger.warning("Отклонено сообщение от user_id=%s", message.from_user.id)
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

    if not card_data.get("purchase_date"):
        from datetime import date
        card_data["purchase_date"] = date.today().isoformat()

    _pending[message.from_user.id] = card_data

    await processing_msg.edit_text(
        _fmt_card(card_data),
        reply_markup=_confirmation_keyboard(),
    )


# ── Callback: подтвердить ─────────────────────────────────────────────────────

@router.callback_query(F.data == "card:confirm")
async def cb_confirm(callback: CallbackQuery):
    if not await _is_allowed(callback.from_user.id):
        await callback.answer()
        return

    card_data = _pending.pop(callback.from_user.id, None)
    if not card_data:
        await callback.answer("Данные устарели. Отправь карту заново.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    try:
        payload = {k: v for k, v in card_data.items() if v is not None}
        await create_card(payload)
        await callback.message.answer("✅ Карта успешно добавлена в панель!")
    except Exception as exc:
        logger.error("Ошибка при создании карты: %s", exc)
        await callback.message.answer(f"❌ Ошибка при сохранении: {exc}")


# ── Callback: исправить ───────────────────────────────────────────────────────

@router.callback_query(F.data == "card:edit")
async def cb_edit(callback: CallbackQuery):
    if not await _is_allowed(callback.from_user.id):
        await callback.answer()
        return

    _pending.pop(callback.from_user.id, None)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "✏️ Хорошо. Отправь данные карты заново в любом удобном формате."
    )


# ── Callback: отмена ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "card:cancel")
async def cb_cancel(callback: CallbackQuery):
    if not await _is_allowed(callback.from_user.id):
        await callback.answer()
        return

    _pending.pop(callback.from_user.id, None)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Отменено.")
