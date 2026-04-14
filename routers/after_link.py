from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings
from data.states import StoryState
from db.crud import add_event
from loader import logger
from utils.common import (
    BUSINESS_TZ,
    copy_template_message,
    copy_template_sequence,
    get_after_link_day_run_time,
)
from utils.scheduler import clear_user_story_jobs, schedule_user_job

router = Router(name='after_link_router')


def get_continue_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Я передумал, хочу продолжить',
                    callback_data='after_link_yes',
                )
            ]
        ]
    )


def _ensure_after_link_templates_configured() -> None:
    required_single_ids = {
        'AFTER_LINK_YES_DELAY_1_MESSAGE_ID': settings.AFTER_LINK_YES_DELAY_1_MESSAGE_ID,
        'AFTER_LINK_YES_DELAY_2_MESSAGE_ID': settings.AFTER_LINK_YES_DELAY_2_MESSAGE_ID,
        'AFTER_LINK_YES_DAY_3_MESSAGE_ID': settings.AFTER_LINK_YES_DAY_3_MESSAGE_ID,
        'AFTER_LINK_YES_DAY_4_MESSAGE_ID': settings.AFTER_LINK_YES_DAY_4_MESSAGE_ID,
        'AFTER_LINK_YES_FOLLOWUP_MESSAGE_ID': settings.AFTER_LINK_YES_FOLLOWUP_MESSAGE_ID,
        'AFTER_LINK_YES_DAY_5_MESSAGE_ID': settings.AFTER_LINK_YES_DAY_5_MESSAGE_ID,
    }
    missing = [name for name, value in required_single_ids.items() if value is None]

    if not settings.after_link_no_message_ids:
        missing.append('AFTER_LINK_NO_MESSAGE_IDS')
    if not settings.after_link_yes_initial_message_ids:
        missing.append('AFTER_LINK_YES_INITIAL_MESSAGE_IDS')
    if settings.TEMPLATE_CHAT_ID is None:
        missing.append('TEMPLATE_CHAT_ID')
    if not settings.after_link_yes_day_1_message_ids:
        missing.append('AFTER_LINK_YES_DAY_1_MESSAGE_IDS')
    if not settings.after_link_yes_day_2_message_ids:
        missing.append('AFTER_LINK_YES_DAY_2_MESSAGE_IDS')

    if missing:
        raise RuntimeError('Missing after-link template config: ' + ', '.join(missing))


async def _handle_config_error(chat_id: int, exc: RuntimeError) -> None:
    logger.error('%s', exc)


async def _schedule_delay_1(chat_id: int) -> None:
    run_date = datetime.now(tz=BUSINESS_TZ) + timedelta(
        seconds=settings.after_link_delay_seconds
    )
    schedule_user_job(
        job_id=f'after_link_yes_delay_1:{chat_id}',
        run_date=run_date,
        func=send_after_link_delay_1,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_delay_1_scheduled:{run_date.isoformat()}',
    )


async def _schedule_delay_2(chat_id: int) -> None:
    run_date = datetime.now(tz=BUSINESS_TZ) + timedelta(
        seconds=settings.after_link_delay_seconds
    )
    schedule_user_job(
        job_id=f'after_link_yes_delay_2:{chat_id}',
        run_date=run_date,
        func=send_after_link_delay_2,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_delay_2_scheduled:{run_date.isoformat()}',
    )


async def _schedule_day_1(chat_id: int) -> None:
    run_date = get_after_link_day_run_time(datetime.now(tz=BUSINESS_TZ))
    schedule_user_job(
        job_id=f'after_link_yes_day_1:{chat_id}',
        run_date=run_date,
        func=send_after_link_day_1,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_day_1_scheduled:{run_date.isoformat()}',
    )


async def _schedule_day_2(chat_id: int) -> None:
    run_date = get_after_link_day_run_time(datetime.now(tz=BUSINESS_TZ))
    schedule_user_job(
        job_id=f'after_link_yes_day_2:{chat_id}',
        run_date=run_date,
        func=send_after_link_day_2,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_day_2_scheduled:{run_date.isoformat()}',
    )


async def _schedule_day_3(chat_id: int) -> None:
    run_date = get_after_link_day_run_time(datetime.now(tz=BUSINESS_TZ))
    schedule_user_job(
        job_id=f'after_link_yes_day_3:{chat_id}',
        run_date=run_date,
        func=send_after_link_day_3,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_day_3_scheduled:{run_date.isoformat()}',
    )


async def _schedule_day_4(chat_id: int) -> None:
    run_date = get_after_link_day_run_time(datetime.now(tz=BUSINESS_TZ))
    schedule_user_job(
        job_id=f'after_link_yes_day_4:{chat_id}',
        run_date=run_date,
        func=send_after_link_day_4,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_day_4_scheduled:{run_date.isoformat()}',
    )


async def _schedule_follow_up(chat_id: int) -> None:
    run_date = datetime.now(tz=BUSINESS_TZ) + timedelta(
        seconds=settings.after_link_follow_up_delay_seconds
    )
    schedule_user_job(
        job_id=f'after_link_yes_follow_up:{chat_id}',
        run_date=run_date,
        func=send_after_link_follow_up,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_follow_up_scheduled:{run_date.isoformat()}',
    )


async def _schedule_day_5(chat_id: int) -> None:
    run_date = get_after_link_day_run_time(datetime.now(tz=BUSINESS_TZ))
    schedule_user_job(
        job_id=f'after_link_yes_day_5:{chat_id}',
        run_date=run_date,
        func=send_after_link_day_5,
        args=[chat_id],
    )
    await add_event(
        tg_id=chat_id,
        event_name=f'after_link_yes_day_5_scheduled:{run_date.isoformat()}',
    )


async def send_after_link_delay_1(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_message(
            chat_id=chat_id,
            message_id=settings.AFTER_LINK_YES_DELAY_1_MESSAGE_ID,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_delay_1_sent')
    await _schedule_delay_2(chat_id)


async def send_after_link_delay_2(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_message(
            chat_id=chat_id,
            message_id=settings.AFTER_LINK_YES_DELAY_2_MESSAGE_ID,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_delay_2_sent')
    await _schedule_day_1(chat_id)


async def send_after_link_day_1(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_sequence(
            chat_id=chat_id,
            message_ids=settings.after_link_yes_day_1_message_ids,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_day_1_sent')
    await _schedule_day_2(chat_id)


async def send_after_link_day_2(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_sequence(
            chat_id=chat_id,
            message_ids=settings.after_link_yes_day_2_message_ids,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_day_2_sent')
    await _schedule_day_3(chat_id)


async def send_after_link_day_3(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_message(
            chat_id=chat_id,
            message_id=settings.AFTER_LINK_YES_DAY_3_MESSAGE_ID,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_day_3_sent')
    await _schedule_day_4(chat_id)


async def send_after_link_day_4(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_message(
            chat_id=chat_id,
            message_id=settings.AFTER_LINK_YES_DAY_4_MESSAGE_ID,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_day_4_sent')
    await _schedule_follow_up(chat_id)


async def send_after_link_follow_up(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_message(
            chat_id=chat_id,
            message_id=settings.AFTER_LINK_YES_FOLLOWUP_MESSAGE_ID,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_follow_up_sent')
    await _schedule_day_5(chat_id)


async def send_after_link_day_5(chat_id: int) -> None:
    try:
        _ensure_after_link_templates_configured()
        await copy_template_message(
            chat_id=chat_id,
            message_id=settings.AFTER_LINK_YES_DAY_5_MESSAGE_ID,
        )
    except RuntimeError as exc:
        await _handle_config_error(chat_id, exc)
        return

    await add_event(tg_id=chat_id, event_name='after_link_yes_day_5_sent')


@router.callback_query(F.data == 'after_link_yes')
async def say_yes_after_link(callback: types.CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest):
        await callback.answer()

    clear_user_story_jobs(tg_id=callback.from_user.id)
    await state.set_state(StoryState.after_link_follow_up)

    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)

    await add_event(tg_id=callback.from_user.id, event_name='after_link_yes')

    try:
        _ensure_after_link_templates_configured()
        await copy_template_sequence(
            chat_id=callback.message.chat.id,
            message_ids=settings.after_link_yes_initial_message_ids,
        )
    except RuntimeError as exc:
        await _handle_config_error(callback.from_user.id, exc)
        return

    await add_event(
        tg_id=callback.from_user.id,
        event_name='after_link_yes_initial_sent',
    )
    await _schedule_delay_1(callback.from_user.id)


@router.callback_query(StoryState.waiting_for_after_link_response, F.data == 'after_link_no')
async def say_no_after_link(callback: types.CallbackQuery, state: FSMContext):
    with suppress(TelegramBadRequest):
        await callback.answer()

    clear_user_story_jobs(tg_id=callback.from_user.id)
    await state.set_state(StoryState.waiting_for_after_link_response)

    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)

    await add_event(tg_id=callback.from_user.id, event_name='after_link_no')

    try:
        _ensure_after_link_templates_configured()
        no_message_ids = settings.after_link_no_message_ids
        if len(no_message_ids) == 1:
            await copy_template_message(
                chat_id=callback.message.chat.id,
                message_id=no_message_ids[0],
                reply_markup=get_continue_kb(),
            )
        else:
            await copy_template_sequence(
                chat_id=callback.message.chat.id,
                message_ids=no_message_ids[:-1],
            )
            await copy_template_message(
                chat_id=callback.message.chat.id,
                message_id=no_message_ids[-1],
                reply_markup=get_continue_kb(),
            )
    except RuntimeError as exc:
        await _handle_config_error(callback.from_user.id, exc)
