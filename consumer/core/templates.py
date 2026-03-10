"""Шаблоны текстов уведомлений по event_type."""

NOTIFICATION_TEMPLATES = {
    "order_created": "Заказ {order_id} создан",
    "order_paid": "Заказ {order_id} оплачен",
    "order_shipped": "Заказ {order_id} отгружен",
    "order_delivered": "Заказ {order_id} доставлен",
    "order_cancelled": "Заказ {order_id} отменён",
}


def render_message(event_type: str, order_id: str) -> str:
    template = NOTIFICATION_TEMPLATES.get(
        event_type, "Заказ {order_id}: событие {event_type}"
    )
    return template.format(order_id=order_id, event_type=event_type)
