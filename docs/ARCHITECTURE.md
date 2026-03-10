# Архитектура сервисов

Проект следует принципам **Clean Architecture** (Robert C. Martin).
Этот документ — обязательный справочник при генерации и ревью кода.

---

## 1. Слои и их ответственность

```
any-service/
├── domain/          # Entities — доменные сущности
├── use_cases/       # Use Cases — бизнес-логика приложения
├── services/        # Interface Adapters — реализации портов (репозитории, Kafka-клиент)
├── api/             # Interface Adapters — HTTP-контроллеры (FastAPI)
├── models/          # Interface Adapters — Pydantic DTO (запросы, ответы, payload)
├── jobs/            # Точки входа — фоновые задачи
├── db/              # Frameworks & Drivers — ORM-модели, миграции, движок БД
├── core/            # Frameworks & Drivers — конфигурация, метрики, логирование
└── main.py          # Composition Root — сборка зависимостей, запуск приложения
```

| Слой | Пакет(ы) | Что содержит |
|------|----------|-------------|
| **Domain** | `domain/` | Чистые dataclass-сущности. Никаких зависимостей от фреймворков, ORM, Pydantic. Только stdlib. |
| **Use Cases** | `use_cases/` | Классы use case с методом `execute`. Протоколы (порты) для инверсии зависимостей. Result-dataclass'ы. |
| **Interface Adapters** | `services/`, `api/`, `models/` | Реализации протоколов (репозитории, Kafka-клиент), HTTP-контроллеры, Pydantic DTO, маппинг domain ↔ ORM / DTO. |
| **Точки входа** | `jobs/` | Фоновые задачи: циклы, вызов use case, сборка зависимостей для job. Запускаются из `main.py`. |
| **Frameworks & Drivers** | `db/`, `core/` | SQLAlchemy ORM-модели, движок БД, конфиг, метрики, логирование. |
| **Composition Root** | `main.py` | Создание и связывание всех зависимостей. Единственное место, где собираются конкретные классы. |

---

## 2. Dependency Rule

Зависимости в исходном коде **направлены только внутрь** — от внешних слоёв к внутренним:

```
Frameworks & Drivers  →  Interface Adapters  →  Use Cases  →  Domain
```

### Запрещено

- `domain/` **не импортирует** ничего из проекта (только stdlib).
- `use_cases/` **не импортирует** из `services/`, `api/`, `db/`, `core/`, `models/`.
- `use_cases/` зависит **только** от `domain/` и от собственных `protocols.py`.

### Разрешено

- `services/` импортирует из `domain/`, `db/`, `use_cases/protocols`.
- `api/` импортирует из `use_cases/`, `models/`, `services/`, `domain/`.
- `main.py` импортирует из любых слоёв (Composition Root).
- `jobs/` импортирует из `services/`, `use_cases/`, `db/`, `core/`.
---

## 3. Порты и адаптеры

Все внешние зависимости use cases описаны **протоколами** (`typing.Protocol`) в `use_cases/protocols.py`:

### Правила

- Новый внешний ресурс (кэш, внешний API, брокер сообщений) → сначала протокол в `use_cases/protocols.py`, затем реализация в `services/`.
- Use case принимает зависимости через конструктор, типизированные протоколами.
- Конкретные классы подставляются только в Composition Root (`main.py`) или в DI-фабриках (`api/`) или точках входа (`jobs/`).

---

## 4. Доменные сущности

- Живут в `domain/`.
- Реализуются как `dataclass` (stdlib) без зависимостей от Pydantic, SQLAlchemy или любых внешних библиотек.
- Use cases оперируют **только** доменными сущностями.
- Маппинг ORM ↔ Domain выполняется внутри адаптера (например, `EventService._to_domain`).

---

## 5. Cross-cutting concerns

| Concern | Где обрабатывается | Где запрещён |
|---------|--------------------|-------------|
| **Метрики** (Prometheus) | `api/`, `jobs/`, `services/`, `core/metrics.py` | `use_cases/`, `domain/`, `main.py` |
| **Логирование** | Допускается в `use_cases/` (stdlib `logging`) | `domain/` |
| **Конфигурация** | `core/config.py` → используется в адаптерах и Composition Root | `use_cases/`, `domain/`, `services/` |

Use cases **не вызывают** метрики напрямую. Вместо этого они возвращают result-объекты (`CreateEventResult`, `RepublishResult`), содержащие достаточно информации для подсчёта метрик вызывающим кодом на уровне адаптера.

---

## 6. Соглашения по коду

### Именование

- Use case → класс с суффиксом `UseCase` и методом `execute` (например, `CreateOrderEventUseCase`).
- Протокол → `typing.Protocol` в `use_cases/protocols.py`.
- Result → `dataclass(frozen=True)` рядом с use case (например, `CreateEventResult`).
- DTO → Pydantic `BaseModel` в `models/` (например, `EventCreate`, `EventRead`).
- ORM-модель → SQLAlchemy модель в `db/schema/` (например, `db/schema/events.Event`).
- Доменная сущность → `dataclass` в `domain/` (например, `domain/events.Event`).

### Маппинг

- `EventRead.from_domain(event)` — domain → response DTO (в `models/`).
- `EventService._to_domain(orm)` — ORM → domain (в `services/`).
- Дублирование ручного маппинга запрещено: один маппер на направление.

### Imports (единообразие)
- Код сервисов (producer, consumer и т.д.): всегда абсолютные импорты от корня проекта, например `from producer.xxx import ...`, `from consumer.xxx import ...` (корень в `pythonpath` в pyproject.toml).
- Тесты: импорты кода приложения — так же от корня (`from producer.xxx`, `from consumer.xxx`). Тестовые утилиты и фабрики — по подпапке тестов: `from tests.producer.factories import ...`, в будущем `from tests.consumer.xxx import ...`. Общие фикстуры можно выносить в `tests/conftest.py` или общий модуль под `tests/`.

---

## 7. Чек-лист при добавлении нового кода

1. Новая бизнес-операция → use case в `use_cases/`, зависимости через протоколы.
2. Новый внешний ресурс → протокол в `protocols.py`, реализация в `services/`.
3. Новая сущность → dataclass в `domain/`, ORM-модель в `db/schema/`, маппер в адаптере.
4. Новый эндпоинт → контроллер в `api/`, метрики в контроллере, не в use case.
5. Проверить: `use_cases/` не импортирует из `db/`, `core/`, `models/`, `services/`, `jobs/`.
