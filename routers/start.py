from contextlib import suppress

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from data.states import StoryState
from data.story_content import text_after_link, text_hello
from db.crud import add_event, add_user
from exception.db import UserNotFound
from loader import logger
from utils.scheduler import clear_user_story_jobs

router = Router(name='start_router')


def _build_subscription_keyboard(
    channels: list[tuple[int, str]],
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for index, (_, chat_url) in enumerate(channels, start=1):
        builder.button(text=f'{index}. Подписаться', url=chat_url)

    builder.button(
        text=f'{len(channels) + 1}. Я подписался',
        callback_data='check_sub',
    )
    builder.adjust(1)
    return builder.as_markup()


@router.message(Command('start'))
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    utm = (command.args or '').strip()
    user_name = (
        message.from_user.username
        or f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    )
    await add_user(tg_id=message.from_user.id, username=user_name, utm_mark=utm)

    clear_user_story_jobs(tg_id=message.from_user.id)
    await state.set_state(StoryState.waiting_for_subscription)

    channels = settings.checked_channels
    if not channels:
        logger.error('Не настроены каналы для проверки подписки в sfbt.env')
        return

    await message.answer(
        text_hello,
        reply_markup=_build_subscription_keyboard(channels),
        parse_mode='HTML',
    )


@router.callback_query(StoryState.waiting_for_subscription, F.data == 'check_sub')
async def verify_subscription(
    callback: types.CallbackQuery,
    bot: Bot,
    state: FSMContext,
):
    with suppress(TelegramBadRequest):
        await callback.answer()

    channels = settings.checked_channels
    missing_channels: list[tuple[int, str]] = []

    for chat_id, chat_url in channels:
        user_sub = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=callback.from_user.id,
        )
        if user_sub.status not in ['member', 'administrator', 'creator']:
            missing_channels.append((chat_id, chat_url))

    if missing_channels:
        await callback.message.answer(
            'Вы подписались не на все каналы.',
            reply_markup=_build_subscription_keyboard(missing_channels),
        )
        return

    try:
        await add_event(
            tg_id=callback.from_user.id,
            event_name='Получить файл: "Пакет Опора и Ресурс"',
        )
    except UserNotFound:
        logger.error(
            'Ошибка: пользователь с tg_id %s не найден в базе.',
            callback.from_user.id,
        )

    after_link_builder = InlineKeyboardBuilder()
    after_link_builder.button(text='Да', callback_data='after_link_yes')
    after_link_builder.button(text='Нет', callback_data='after_link_no')
    after_link_builder.adjust(2)

    await state.set_state(StoryState.waiting_for_after_link_response)
    await callback.message.answer(f'Ваша ссылка: {settings.RESOURCE_LINK}')
    await callback.message.answer(
        text_after_link,
        reply_markup=after_link_builder.as_markup(),
        parse_mode='HTML',
    )
