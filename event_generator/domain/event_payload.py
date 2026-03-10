from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EventPayload:
    order_id: str
    user_id: str
    event_type: str
    event_occurred_at: datetime
