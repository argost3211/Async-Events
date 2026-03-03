import enum

from pydantic import BaseModel, Field


class EventType(str, enum.Enum):
    user_registered = "user_registered"


class EventCreate(BaseModel):
    type: EventType
    message: str = Field(max_length=1000)


class EventRead(BaseModel):
    id: str
    type: EventType
    message: str = Field(max_length=1000)
