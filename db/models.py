from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class SfbtUser(Base):
    __tablename__ = "sfbt_users"

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100))
    join_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    utm_mark: Mapped[str | None] = mapped_column(String(100), nullable=True)

    events: Mapped[list["SfbtEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class SfbtEvent(Base):
    __tablename__ = "sfbt_events"

    user_id: Mapped[int] = mapped_column(ForeignKey("sfbt_users.id"), nullable=False)
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["SfbtUser"] = relationship(back_populates="events")
