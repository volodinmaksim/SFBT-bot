from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import settings
from db.db_helper import db_helper
from db.models import SfbtUser
from loader import logger, scheduler
from utils.common import copy_template_message

BUSINESS_TZ = ZoneInfo("Europe/Moscow")

TEST_TG_ID = 846222946
FIRST_MESSAGE_ID = 36
SECOND_MESSAGE_ID = 37
GAP_SECONDS = 30.0

TEST_RUN_AT = datetime(2026, 4, 10, 0, 10, 0, tzinfo=BUSINESS_TZ)
BROADCAST_RUN_AT = datetime(2026, 4, 10, 12, 0, 0, tzinfo=BUSINESS_TZ)


async def send_sequence_to_user(
    tg_id: int,
    first_message_id: int = FIRST_MESSAGE_ID,
    second_message_id: int = SECOND_MESSAGE_ID,
    gap_seconds: float = GAP_SECONDS,
) -> None:
    for message_id in (first_message_id, second_message_id):
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

        if message_id == first_message_id:
            await asyncio.sleep(gap_seconds)


async def get_all_user_ids() -> list[int]:
    async with db_helper.session() as session:
        result = await session.execute(select(SfbtUser.tg_id).order_by(SfbtUser.id.asc()))
        return list(result.scalars())


def schedule_job(*, job_id: str, run_at: datetime, tg_id: int) -> None:
    scheduler.add_job(
        "scripts.broadcast_templates:send_sequence_to_user",
        trigger="date",
        run_date=run_at.astimezone(scheduler.timezone),
        args=[tg_id, FIRST_MESSAGE_ID, SECOND_MESSAGE_ID, GAP_SECONDS],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=12 * 60 * 60,
        coalesce=True,
        max_instances=1,
    )


async def main() -> None:
    if settings.TEMPLATE_CHAT_ID is None:
        raise SystemExit("TEMPLATE_CHAT_ID is not configured")

    user_ids = await get_all_user_ids()
    if not user_ids:
        logger.warning("No users found")
        return

    scheduler.start(paused=True)
    try:
        for tg_id in user_ids:
            schedule_job(
                job_id=f"broadcast_all:{tg_id}:{BROADCAST_RUN_AT.strftime('%Y%m%dT%H%M%S')}",
                run_at=BROADCAST_RUN_AT,
                tg_id=tg_id,
            )

        schedule_job(
            job_id=f"broadcast_test:{TEST_TG_ID}:{TEST_RUN_AT.strftime('%Y%m%dT%H%M%S')}",
            run_at=TEST_RUN_AT,
            tg_id=TEST_TG_ID,
        )
        logger.info(
            "Scheduled %s jobs for %s and test for %s at %s",
            len(user_ids),
            BROADCAST_RUN_AT.isoformat(),
            TEST_TG_ID,
            TEST_RUN_AT.isoformat(),
        )
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
