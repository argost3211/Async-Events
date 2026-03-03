import enum
from datetime import datetime

from pydantic import BaseModel, Field


class EventType(str, enum.Enum):
    user_registered = "user_registered"
    password_changed = "password_changed"
    email_changed = "email_changed"


class EventCreate(BaseModel):
    type: EventType
    message: str = Field(max_length=1000)


class EventRead(BaseModel):
    id: str
    type: EventType
    message: str = Field(max_length=1000)
    created_at: datetime
