from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from .base import Base, uuid_pk, created_at


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid_pk]
    user_id: Mapped[str] = mapped_column(String(length=64), nullable=False)
    order_id: Mapped[str] = mapped_column(String(length=64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(length=32), nullable=False)
    message: Mapped[str] = mapped_column(String(length=512), nullable=False)
    created_at: Mapped[created_at]

    def __repr__(self) -> str:
        return (
            f"Notification(id={self.id}, order_id={self.order_id}, "
            f"event_type={self.event_type}, created_at={self.created_at})"
        )
