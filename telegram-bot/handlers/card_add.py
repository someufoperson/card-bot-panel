import logging
import re
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.api_client import card_number_exists, create_card, delete_pending, get_donor_chat_ids, get_pending, get_setting, save_pending
from services.gemini_client import gemini_client
from config import settings

# Сообщение считается потенциальной картой если содержит 16 цифр
# (возможно с пробелами/дефисами между группами по 4)
_RE_CARD = re.compile(r'\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}')
_INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

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


def _safe_name(name: str) -> str:
    return _INVALID_PATH_CHARS.sub('_', name).strip() or 'unknown'


async def _save_photo(bot: Bot, file_id: str, card_data: dict) -> None:
    """Скачивает фото по file_id и сохраняет в папку {data_folder}/{ФИО}/{банк}_{номер}.jpg"""
    try:
        data_folder = await get_setting("data_folder")
        base = Path(data_folder) if data_folder else Path("logs") / "drops"
        folder = base / _safe_name(card_data.get("full_name") or "unknown")
        folder.mkdir(parents=True, exist_ok=True)

        bank = _safe_name(card_data.get("bank") or "bank")
        card_number = re.sub(r"\D", "", card_data.get("card_number") or "")
        filename = f"{bank}_{card_number}.jpg"

        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, destination=str(folder / filename))
    except Exception as exc:
        logger.warning("Не удалось сохранить фото: %s", exc)


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

    if message.chat.type != "private":
        donor_ids = await get_donor_chat_ids()
        if str(message.chat.id) not in donor_ids:
            return

    card_number = re.sub(r"\D", "", _RE_CARD.search(message.text).group())
    if await card_number_exists(card_number):
        await message.answer(f"⚠️ Карта *{card_number[-4:]} уже есть в базе.")
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


# ── Фото из группы-донора ─────────────────────────────────────────────────────

@router.message(F.photo)
async def handle_photo(message: Message):
    if message.chat.type != "private":
        donor_ids = await get_donor_chat_ids()
        if str(message.chat.id) not in donor_ids:
            return

    caption = message.caption or ""
    if not _looks_like_card(caption):
        return

    card_number = re.sub(r"\D", "", _RE_CARD.search(caption).group())
    if await card_number_exists(card_number):
        await message.answer(f"⚠️ Карта *{card_number[-4:]} уже есть в базе.")
        return

    if not settings.gemini_api_key:
        await message.answer("⚠️ Gemini API ключ не настроен. Укажи его в настройках панели.")
        return

    processing_msg = await message.answer("⏳ Распознаю данные карты…")
    card_data = await gemini_client.parse_card(caption)

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
    card_data["_photo_file_id"] = message.photo[-1].file_id

    await save_pending(processing_msg.message_id, message.from_user.id, card_data)
    await processing_msg.edit_text(
        _fmt_card(card_data),
        reply_markup=_confirmation_keyboard(processing_msg.message_id),
    )


# ── Callback: подтвердить ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("card:confirm:"))
async def cb_confirm(callback: CallbackQuery, bot: Bot):
    msg_id = int(callback.data.split(":")[-1])
    card_data = await get_pending(msg_id)
    if not card_data:
        await callback.answer("Данные устарели. Отправь карту заново.", show_alert=True)
        return

    await delete_pending(msg_id)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    photo_file_id = card_data.pop("_photo_file_id", None)

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
        if photo_file_id:
            await _save_photo(bot, photo_file_id, card_data)
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
