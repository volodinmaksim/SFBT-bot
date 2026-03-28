from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings


class DataBaseHelper:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, Any]:
        async with self.session_factory() as session:
            yield session


db_helper = DataBaseHelper(settings.DB_URL)
