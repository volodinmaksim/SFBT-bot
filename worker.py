import asyncio
import contextlib
from db.db_helper import db_helper
from db.models import Base
from loader import bot, dp, logger, redis, scheduler
from routers import after_link_router, start_router


async def init_db() -> None:
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def register_routers() -> None:
    dp.include_router(start_router)
    dp.include_router(after_link_router)
async def main() -> None:
    await init_db()
    register_routers()
    scheduler.start()
    with contextlib.suppress(Exception):
        await bot.delete_webhook(drop_pending_updates=False)
    logger.info('Starting polling for sfbt bot')
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        with contextlib.suppress(Exception):
            scheduler.shutdown()
        with contextlib.suppress(Exception):
            asyncio.run(dp.storage.close())
        with contextlib.suppress(Exception):
            if redis is not None:
                asyncio.run(redis.aclose())
