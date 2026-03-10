from dataclasses import dataclass

CHAIN: tuple[str, ...] = (
    "order_created",
    "order_paid",
    "order_shipped",
    "order_delivered",
)


@dataclass
class OrderChain:
    order_id: str
    user_id: str
    current_step: int = 0
    cancelled: bool = False
    completed: bool = False

    def next_event_type(self) -> str | None:
        if self.cancelled:
            return "order_cancelled"
        if self.current_step >= len(CHAIN):
            return None
        return CHAIN[self.current_step]

    def advance(self) -> None:
        if self.cancelled or self.completed:
            return
        self.current_step += 1
        if self.current_step >= len(CHAIN):
            self.completed = True

    def cancel(self) -> None:
        self.cancelled = True
        self.completed = True
