from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from .base import Base, uuid_pk, created_at


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid_pk]
    type: Mapped[str] = mapped_column(String(length=64), nullable=False)
    message: Mapped[str | None]
    created_at: Mapped[created_at]
