## Миграции

### Пример изменения таблицы 1
- В таблицу Y добавлено новое поле X

#### Хорошее сообщение миграции
- add column X to table Y

#### Плохое сообщение миграции
- change table Y

### Пример изменения таблицы 2
- В таблицу Y добавлено ограничение уникальности для поля X

#### Хорошее сообщение миграции
- add unique constraint on Y for column X

## Названия переменных

### Переменные не должны иметь в названии технологию, кроме переменных в конфигах и настройках, которые напрямую определяют настройки конкретной технологии
#### Плохое название
- kafka_client

#### Хорошее название
- broker_client

#### Плохое название
- broker_connect_retry_attempts

#### Хорошее название
- kafka_connect_retry_attempts


## Комментарии в классах

### Good
```
class CreateOrderEventUseCase:
    """
    Создание события заказа: только запись в БД.
    Возвращает CreateEventResult.
    """

    def __init__(
        self,
        event_repo: EventRepository,
        kafka_publisher: EventPublisher | None = None,
    ) -> None:
        self._event_repo = event_repo
        self._kafka_publisher = kafka_publisher

    async def execute(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> CreateEventResult:
        event = await self._event_repo.create_event(
            order_id=order_id,
            user_id=user_id,
            event_type=event_type,
            event_occurred_at=event_occurred_at,
        )
        return CreateEventResult(event=event, published=False)
```

### Bad
```
class CreateOrderEventUseCase:
    """
    Создание события заказа: только запись в БД.
    Возвращает CreateEventResult. Публикация в Kafka выполняется в фоне (API).
    """

    def __init__(
        self,
        event_repo: EventRepository,
        kafka_publisher: EventPublisher | None = None,
    ) -> None:
        self._event_repo = event_repo
        self._kafka_publisher = kafka_publisher

    async def execute(
        self,
        order_id: str,
        user_id: str,
        event_type: str,
        event_occurred_at: datetime,
    ) -> CreateEventResult:
        event = await self._event_repo.create_event(
            order_id=order_id,
            user_id=user_id,
            event_type=event_type,
            event_occurred_at=event_occurred_at,
        )
        return CreateEventResult(event=event, published=False)
```