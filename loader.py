import logging
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiohttp import BasicAuth
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s %(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

session = AiohttpSession(
    proxy=(
        f'socks5://{settings.PROXY_IP_OR_DOMAIN}:{settings.PROXY_PORT}',
        BasicAuth(
            settings.PROXY_LOGIN,
            settings.PROXY_PASSWORD.get_secret_value(),
        ),
    )
)

bot = Bot(
    token=settings.active_bot_token.get_secret_value(),
    session=session,
)

if settings.TEST_MODE:
    logger.warning(
        'Test mode is enabled: using shortened delays (%ss / %ss)',
        settings.after_link_delay_seconds,
        settings.after_link_day_delay_seconds,
    )


if settings.REDIS_URL:
    redis = Redis.from_url(settings.REDIS_URL)
    logger.info('FSM storage: Redis (%s)', settings.REDIS_URL)
    dp = Dispatcher(storage=RedisStorage(redis=redis))
else:
    redis = None
    logger.warning('FSM storage: MemoryStorage (REDIS_URL is not set)')
    dp = Dispatcher(storage=MemoryStorage())


if settings.REDIS_URL:
    redis_url = urlparse(settings.REDIS_URL)
    redis_db = int(redis_url.path.lstrip('/') or '0')
    scheduler_jobstores = {
        'default': RedisJobStore(
            jobs_key='apscheduler.jobs',
            run_times_key='apscheduler.run_times',
            host=redis_url.hostname or 'localhost',
            port=redis_url.port or 6379,
            db=redis_db,
            password=redis_url.password,
        )
    }
    logger.info(
        'Scheduler jobstore: Redis (%s:%s/%s)',
        redis_url.hostname or 'localhost',
        redis_url.port or 6379,
        redis_db,
    )
else:
    scheduler_jobstores = {'default': MemoryJobStore()}
    logger.warning('Scheduler jobstore: MemoryJobStore (REDIS_URL is not set)')

scheduler = AsyncIOScheduler(timezone=ZoneInfo('UTC'), jobstores=scheduler_jobstores)
