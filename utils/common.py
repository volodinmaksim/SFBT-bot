from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup

from config import settings
from loader import bot

BUSINESS_TZ = ZoneInfo('Europe/Moscow')
BUSINESS_DAY_START = 10
BUSINESS_DAY_END = 21


def get_next_business_time(base_time: datetime | None = None) -> datetime:
    if base_time is None:
        base_time = datetime.now(tz=BUSINESS_TZ)
    elif base_time.tzinfo is None:
        raise ValueError('base_time must be timezone-aware')
    else:
        base_time = base_time.astimezone(BUSINESS_TZ)

    run_date = base_time + timedelta(days=1)
    if run_date.hour < BUSINESS_DAY_START:
        return run_date.replace(
            hour=BUSINESS_DAY_START,
            minute=0,
            second=0,
            microsecond=0,
        )

    too_late = run_date.hour > BUSINESS_DAY_END or (
        run_date.hour == BUSINESS_DAY_END
        and (run_date.minute > 0 or run_date.second > 0 or run_date.microsecond > 0)
    )
    if too_late:
        return run_date.replace(
            hour=BUSINESS_DAY_END,
            minute=0,
            second=0,
            microsecond=0,
        )

    return run_date


def get_after_link_day_run_time(base_time: datetime | None = None) -> datetime:
    if base_time is None:
        base_time = datetime.now(tz=BUSINESS_TZ)
    elif base_time.tzinfo is None:
        raise ValueError('base_time must be timezone-aware')
    else:
        base_time = base_time.astimezone(BUSINESS_TZ)

    if settings.TEST_MODE:
        return base_time + timedelta(seconds=settings.after_link_day_delay_seconds)

    return get_next_business_time(base_time)


def _require_template_chat_id() -> int:
    if settings.TEMPLATE_CHAT_ID is None:
        raise RuntimeError('TEMPLATE_CHAT_ID is not configured')
    return settings.TEMPLATE_CHAT_ID


async def copy_template_message(
    *,
    chat_id: int,
    message_id: int,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    await bot.copy_message(
        chat_id=chat_id,
        from_chat_id=_require_template_chat_id(),
        message_id=message_id,
        reply_markup=reply_markup,
    )


async def copy_template_sequence(chat_id: int, message_ids: Sequence[int]) -> None:
    template_ids = list(message_ids)
    if not template_ids:
        raise RuntimeError('Template message ids are not configured')

    template_chat_id = _require_template_chat_id()
    if len(template_ids) == 1:
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=template_chat_id,
            message_id=template_ids[0],
        )
        return

    await bot.copy_messages(
        chat_id=chat_id,
        from_chat_id=template_chat_id,
        message_ids=template_ids,
    )
