import uuid
import datetime
from typing import Annotated
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import DateTime, text


class Base(AsyncAttrs, DeclarativeBase):
    pass


uuid_pk = Annotated[
    uuid.UUID, mapped_column(UUID, primary_key=True, default=uuid.uuid4)
]
created_at = Annotated[
    datetime.datetime,
    mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    ),
]
