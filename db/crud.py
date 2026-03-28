from sqlalchemy import select

from db.db_helper import db_helper
from db.models import SfbtEvent, SfbtUser
from exception.db import UserNotFound


async def add_user(tg_id: int, username: str, utm_mark: str) -> None:
    async with db_helper.session() as session:
        user = await get_user(tg_id, session=session)
        if user is None:
            session.add(SfbtUser(tg_id=tg_id, username=username, utm_mark=utm_mark))
            await session.commit()


async def get_user(tg_id: int, session=None):
    owns_session = session is None
    if owns_session:
        async with db_helper.session() as session:
            query = select(SfbtUser).where(SfbtUser.tg_id == tg_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    query = select(SfbtUser).where(SfbtUser.tg_id == tg_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def add_event(tg_id: int, event_name: str) -> None:
    async with db_helper.session() as session:
        user_query = await session.execute(select(SfbtUser.id).where(SfbtUser.tg_id == tg_id))
        internal_user_id = user_query.scalar()

        if internal_user_id is None:
            raise UserNotFound

        session.add(SfbtEvent(user_id=internal_user_id, event_name=event_name))
        await session.commit()
