from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select

from config import settings
from db.db_helper import db_helper
from db.models import SfbtUser
from loader import bot, logger, redis, scheduler
from utils.common import copy_template_message
from utils.scheduler import schedule_user_job

BUSINESS_TZ = ZoneInfo("Europe/Moscow")
TEST_RUN_AT = datetime(2026, 4, 9, 23, 35, 0, tzinfo=BUSINESS_TZ)
BROADCAST_RUN_AT = datetime(2026, 4, 10, 12, 0, 0, tzinfo=BUSINESS_TZ)
TEST_TG_ID = 846222946
FIRST_MESSAGE_ID = 36
SECOND_MESSAGE_ID = 37
GAP_SECONDS = 30.0


async def get_target_ids(target_tg_id: int | None) -> list[int]:
    if target_tg_id is not None:
        return [target_tg_id]

    async with db_helper.session() as session:
        result = await session.execute(
            select(SfbtUser.tg_id).order_by(SfbtUser.id.asc())
        )
        return list(result.scalars())


async def send_sequence_to_user(tg_id: int) -> None:
    for message_id in (FIRST_MESSAGE_ID, SECOND_MESSAGE_ID):
        while True:
            try:
                await copy_template_message(chat_id=tg_id, message_id=message_id)
                break
            except TelegramRetryAfter as exc:
                await asyncio.sleep(float(exc.retry_after))
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                logger.warning(
                    "Skip tg_id=%s for message_id=%s: %s: %s",
                    tg_id,
                    message_id,
                    exc.__class__.__name__,
                    exc,
                )
                return

        if message_id == FIRST_MESSAGE_ID:
            await asyncio.sleep(GAP_SECONDS)


def build_job_id(prefix: str, tg_id: int, run_at: datetime) -> str:
    return f"{prefix}:{tg_id}:{run_at.strftime('%Y%m%dT%H%M%S')}"


def schedule_jobs_for_users(target_ids: list[int], run_at: datetime, prefix: str) -> None:
    for tg_id in target_ids:
        schedule_user_job(
            job_id=build_job_id(prefix, tg_id, run_at),
            run_date=run_at,
            func=send_sequence_to_user,
            args=[tg_id],
        )


async def schedule_broadcasts() -> None:
    if settings.TEMPLATE_CHAT_ID is None:
        raise SystemExit("TEMPLATE_CHAT_ID is not configured")

    all_target_ids = await get_target_ids(target_tg_id=None)
    if not all_target_ids:
        logger.warning("No users found for broadcast")
        return

    scheduler.start(paused=True)
    try:
        schedule_jobs_for_users(all_target_ids, BROADCAST_RUN_AT, "broadcast_all")
        schedule_jobs_for_users([TEST_TG_ID], TEST_RUN_AT, "broadcast_test")
        logger.info(
            "Scheduled %s user jobs for %s and test job for tg_id=%s at %s",
            len(all_target_ids),
            BROADCAST_RUN_AT.isoformat(),
            TEST_TG_ID,
            TEST_RUN_AT.isoformat(),
        )
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    try:
        asyncio.run(schedule_broadcasts())
    finally:
        asyncio.run(bot.session.close())
        if redis is not None:
            asyncio.run(redis.aclose())
