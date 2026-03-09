from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Event:
    id: UUID
    order_id: str
    user_id: str
    event_type: str
    created_at: datetime
    event_occurred_at: datetime
    published_to_kafka: bool
