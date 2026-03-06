import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime

from .base import Base, uuid_pk, created_at


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid_pk]
    order_id: Mapped[str] = mapped_column(String(length=64), nullable=False)
    user_id: Mapped[str] = mapped_column(String(length=64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(length=32), nullable=False)
    created_at: Mapped[created_at]
    event_occurred_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    published_to_kafka: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return (
            f"Event(id={self.id}, order_id={self.order_id}, event_type={self.event_type}, "
            f"published_to_kafka={self.published_to_kafka})"
        )
