from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class HabitLog(Base):
    __tablename__ = "habit_logs"

    __table_args__ = (
        UniqueConstraint("log_date", "habit", name="uq_habitlog_date_habit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    habit: Mapped[str] = mapped_column(String(100), index=True)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
