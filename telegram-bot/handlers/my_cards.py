import asyncio
import logging
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import settings as bot_settings
from services.api_client import (
    block_card, get_all_cards, get_card_by_id, get_cards_by_user,
    get_setting, unblock_card,
)

logger = logging.getLogger(__name__)
router = Router()

PAGE_SIZE = 10


# ── Helpers ──────────────────────────────────────────────────────────────────

def _normalize_username(user) -> str | None:
    return f"@{user.username}" if user.username else None


async def _is_admin(user_id: int) -> bool:
    from_api = await get_setting("allowed_user_id")
    allowed = (from_api or bot_settings.telegram_allowed_user_id).strip()
    return bool(allowed) and str(user_id) == allowed


def _fmt_date(d: str | None) -> str:
    if not d:
        return "—"
    try:
        return date.fromisoformat(d[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return d


def _fmt_number(number: str | None) -> str:
    if not number:
        return "—"
    if len(number) == 16 and number.isdigit():
        return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:]}"
    return number


def _list_text(label: str, total: int, page: int) -> str:
    total_pages = max(1, -(-total // PAGE_SIZE))
    return f"{label} ({total})  —  стр. {page}/{total_pages}:"


def _sort_cards(cards: list[dict]) -> list[dict]:
    return sorted(cards, key=lambda c: 1 if c.get("active_block") else 0)


def _list_keyboard(cards: list[dict], page: int, total: int) -> InlineKeyboardMarkup:
    total_pages = max(1, -(-total // PAGE_SIZE))
    buttons = [
        [InlineKeyboardButton(
            text=f"{c['full_name']} | {c['bank'] or '—'}",
            callback_data=f"mycard:d:{c['id']}:{page}",
            style="danger" if c.get("active_block") else "success",
        )]
        for c in cards
    ]
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="← Пред.", callback_data=f"mycards:p:{page - 1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="След. →", callback_data=f"mycards:p:{page + 1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _detail_text(card: dict, device_domain: str | None = None, is_admin: bool = False) -> str:
    block = card.get("active_block")
    device = card.get("device")

    lines = [
        f"<b>{card.get('full_name') or '—'}</b>",
        "",
        f"🏦 Банк: {card.get('bank') or '—'}",
        f"💳 Карта: <code>{_fmt_number(card.get('card_number'))}</code>",
        f"📱 Телефон: {card.get('phone_number') or '—'}",
    ]

    if is_admin:
        lines.append(f"👤 Пользователь: {card.get('responsible_user') or '—'}")
        lines.append(f"🗂 Группа: {card.get('group_name') or '—'}")

    lines += [
        "",
        f"💰 Баланс: {card.get('balance') or '0'}",
        f"📊 Оборот за месяц: {card.get('monthly_turnover') or '0'}",
        "",
        f"📅 Дата покупки: {_fmt_date(card.get('purchase_date'))}",
        f"📦 Дата забора: {_fmt_date(card.get('pickup_date'))}",
    ]

    if is_admin:
        lines.append(f"🗓 Добавлена: {_fmt_date(card.get('created_at'))}")

    lines += [
        "",
        f"🔒 Блокировка: {'<b>Заблокирована</b> с ' + _fmt_date(block['blocked_at']) if block else 'Нет'}",
    ]

    if device:
        serial = device.get("serial")
        if serial and device_domain:
            url = f"{device_domain.rstrip('/')}/{serial}"
            lines.append(f"🔗 <code>{url}</code>")

    if card.get("comment"):
        lines.append(f"\n💬 {card['comment']}")

    return "\n".join(lines)


def _detail_keyboard(card_id: str, back_page: int, is_blocked: bool) -> InlineKeyboardMarkup:
    if is_blocked:
        block_btn = InlineKeyboardButton(
            text="🟢 Разблокировать",
            callback_data=f"mycard:unblock:{card_id}:{back_page}",
            style="success",
        )
    else:
        block_btn = InlineKeyboardButton(
            text="🔴 Заблокировать",
            callback_data=f"mycard:block:{card_id}:{back_page}",
            style="danger",
        )
    return InlineKeyboardMarkup(inline_keyboard=[
        [block_btn],
        [InlineKeyboardButton(text="← Назад", callback_data=f"mycard:b:{back_page}")],
    ])


async def _edit_or_send(target, text: str, keyboard: InlineKeyboardMarkup):
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            return
        except Exception:
            msg = target.message
    else:
        msg = target
    await msg.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def _fetch_cards_for_user(user_id: int, username: str | None) -> tuple[list[dict], str]:
    """Возвращает (карты, заголовок). Для админа — все карты."""
    if await _is_admin(user_id):
        cards = await get_all_cards()
        return cards, "Все карты"
    if username:
        cards = await get_cards_by_user(username)
        return cards, f"Карты пользователя {username}"
    return [], ""


# ── /card ─────────────────────────────────────────────────────────────────────

@router.message(Command("card"))
async def cmd_my_cards(message: Message):
    username = _normalize_username(message.from_user)
    cards, label = await _fetch_cards_for_user(message.from_user.id, username)

    if not label:
        await message.answer(
            "⚠️ У тебя не задан username в Telegram. "
            "Попроси администратора добавить карты вручную."
        )
        return

    if not cards:
        await message.answer(f"У пользователя {username} нет привязанных карт.")
        return

    total = len(cards)
    cards = _sort_cards(cards)
    page_cards = cards[:PAGE_SIZE]
    await message.answer(
        _list_text(label, total, 1),
        reply_markup=_list_keyboard(page_cards, 1, total),
        parse_mode="HTML",
    )


# ── Пагинация списка ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("mycards:p:"))
async def cb_list_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[-1])
    username = _normalize_username(callback.from_user)
    cards, label = await _fetch_cards_for_user(callback.from_user.id, username)

    if not label:
        await callback.answer("Не удалось определить пользователя.", show_alert=True)
        return

    total = len(cards)
    cards = _sort_cards(cards)
    page_cards = cards[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    await callback.answer()
    await _edit_or_send(callback, _list_text(label, total, page), _list_keyboard(page_cards, page, total))


# ── Детали карты ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("mycard:d:"))
async def cb_card_detail(callback: CallbackQuery):
    _, _, card_id, back_page = callback.data.split(":")
    card, domain_from_settings, admin = await asyncio.gather(
        get_card_by_id(card_id),
        get_setting("device_domain"),
        _is_admin(callback.from_user.id),
    )
    if not card:
        await callback.answer("Карта не найдена.", show_alert=True)
        return

    device_domain = domain_from_settings or bot_settings.device_domain
    is_blocked = card.get("active_block") is not None

    await callback.answer()
    await _edit_or_send(
        callback,
        _detail_text(card, device_domain, is_admin=admin),
        _detail_keyboard(card_id, int(back_page), is_blocked),
    )


# ── Блокировка / Разблокировка ───────────────────────────────────────────────

async def _render_detail(callback: CallbackQuery, card_id: str, back_page: int) -> None:
    card, domain_from_settings, admin = await asyncio.gather(
        get_card_by_id(card_id),
        get_setting("device_domain"),
        _is_admin(callback.from_user.id),
    )
    if not card:
        await callback.answer("Карта не найдена.", show_alert=True)
        return
    device_domain = domain_from_settings or bot_settings.device_domain
    is_blocked = card.get("active_block") is not None
    await callback.answer()
    await _edit_or_send(
        callback,
        _detail_text(card, device_domain, is_admin=admin),
        _detail_keyboard(card_id, back_page, is_blocked),
    )


@router.callback_query(F.data.startswith("mycard:block:"))
async def cb_block(callback: CallbackQuery):
    _, _, card_id, back_page = callback.data.split(":")
    try:
        await block_card(card_id)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return
    await _render_detail(callback, card_id, int(back_page))


@router.callback_query(F.data.startswith("mycard:unblock:"))
async def cb_unblock(callback: CallbackQuery):
    _, _, card_id, back_page = callback.data.split(":")
    try:
        await unblock_card(card_id)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return
    await _render_detail(callback, card_id, int(back_page))


# ── Кнопка "Назад" ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("mycard:b:"))
async def cb_back_to_list(callback: CallbackQuery):
    page = int(callback.data.split(":")[-1])
    username = _normalize_username(callback.from_user)
    cards, label = await _fetch_cards_for_user(callback.from_user.id, username)

    if not label:
        await callback.answer("Не удалось определить пользователя.", show_alert=True)
        return

    total = len(cards)
    cards = _sort_cards(cards)
    page_cards = cards[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    await callback.answer()
    await _edit_or_send(callback, _list_text(label, total, page), _list_keyboard(page_cards, page, total))
