from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Notification:
    id: UUID
    user_id: str
    order_id: str
    event_type: str
    message: str
    created_at: datetime
