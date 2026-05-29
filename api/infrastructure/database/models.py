from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AppScore(Base):
    __tablename__ = "app_score"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_user.id"))
    games: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    game_type: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped[AppUser] = relationship(back_populates="scores")


class AppUser(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(48), default="WithOUtName")
    name: Mapped[str] = mapped_column(String(48), default="WithOUtUsernName")
    joined_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    lang_code: Mapped[str] = mapped_column(String(2), default="fa")

    scores: Mapped[list[AppScore]] = relationship(back_populates="user")


class AppGame(Base):
    __tablename__ = "app_game"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mid: Mapped[str] = mapped_column(String(48))
    player_1_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_user.id"),
        nullable=True,
    )
    player_2_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_user.id"),
        nullable=True,
    )
    type: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(10))
    played_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player_1: Mapped[AppUser | None] = relationship(foreign_keys=[player_1_id])
    player_2: Mapped[AppUser | None] = relationship(foreign_keys=[player_2_id])


class AppSponser(Base):
    __tablename__ = "app_sponser"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    link: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    joined_memebers: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_time: Mapped[date] = mapped_column(Date, default=date.today)
