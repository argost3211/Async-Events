# План реализации проекта (события заказов и уведомления)

---

## Порядок реализации (общая последовательность)

1. **Инфраструктура и общая схема БД** — чтобы Producer и Consumer могли работать с одной БД.
2. **Producer** — довести до контракта «события заказов»: модель, Kafka, фоновый job, health, метрики.
3. **Consumer** — с нуля: подписка на Kafka, идемпотентность, уведомления, retry, DLQ, метрики.
4. **Event generator** — генерация нагрузки и дубликатов.
5. **Мониторинг** — Prometheus, Grafana, дашборды.
6. **Docker Compose** — все сервисы, зависимости, healthcheck.

---

# 1. Инфраструктура и общая база данных

## 1.1. Конфигурация окружения

- [ ] В `.env.example` задать переменные для всех сервисов:
  - Postgres: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
  - Kafka: хост/порт брокера для Producer и Consumer.
  - При необходимости — отдельные порты для приложений (Producer, Consumer).
- [ ] Убедиться, что Producer и Consumer используют один и тот же connection string к Postgres (общий `.env` / `env_file` в docker-compose).

## 1.2. Схема БД (одна для Producer и Consumer)

- [ ] **Общая схема и миграции** размещаются в **`shared/db/`**:
  - `shared/db/schema/` — модели SQLAlchemy (Base, Event, Notification), используются и Producer, и Consumer.
  - `shared/db/migrations/` — Alembic (env.py, script.py.mako, versions/); одна история миграций для обоих сервисов.
- [ ] **Таблица событий заказов (events)**  
  Используется Producer. Поля:
  - `id` (UUID, PK),
  - `order_id` (строка/UUID),
  - `user_id` (строка/UUID),
  - `event_type` (enum/строка: `order_created`, `order_paid`, `order_shipped`, `order_delivered`, `order_cancelled`),
  - `created_at` (время создания записи в БД),
  - `event_occurred_at` (время наступления события из API),
  - `published_to_kafka` (boolean, по умолчанию `false`).
- [ ] **Таблица уведомлений (notifications)**  
  Используется Consumer. Поля:
  - `id` (UUID, PK),
  - `user_id`, `order_id`, `event_type`, `message`, `created_at`.
- [ ] Producer и Consumer подключаются к БД через свой движок/сессии (например, `producer/db/engine.py`), но **импортируют модели из `shared.db.schema`**. Запуск миграций — из корня проекта: `alembic upgrade head` (Alembic читает URL из env: POSTGRES_*).

## 1.3. Docker: БД и Kafka

- [ ] В `docker-compose.yml` сервисы `db` (Postgres) и `broker` (Kafka) без зависимостей друг от друга, поднимаются первыми.
- [ ] Для Kafka задать параметры (уже есть в текущем `docker-compose`); при необходимости добавить переменные для доступа с хоста контейнеров (например, `KAFKA_ADVERTISED_LISTENERS` с именем сервиса `broker`).

---

# 2. Producer

**Уже есть:** FastAPI-приложение, роутер `/api/v1/events`, сохранение «события» в Postgres, слой сервисов, конфиг, движок БД, миграции, таблица `events` (id, type, message, created_at).

**Нужно:** перевести домен на «события заказов», добавить публикацию в Kafka, фоновый job повтора, создание топиков, healthcheck и метрики.

## 2.1. Модель данных и API (события заказов)

- [ ] **Pydantic-модель** (единая для API и для payload в Kafka):
  - `order_id`, `user_id`, `event_type`, `event_occurred_at`;
  - `event_type` — Literal/Enum: `order_created`, `order_paid`, `order_shipped`, `order_delivered`, `order_cancelled`.
- [ ] Заменить/расширить модели в `producer/models/`: входная модель для `POST /api/v1/events` и модель ответа (например, 201 с `id` сохранённой записи).
- [ ] Схема БД (модель `Event`) находится в **`shared/db/schema/events.py`**; миграции — в **`shared/db/migrations/`** (см. п. 1.2).

## 2.2. Бизнес-логика приёма события

- [ ] **Порядок операций:**  
  1) Валидация тела запроса (Pydantic).  
  2) В транзакции: запись в Postgres (таблица `events`).  
  3) После успешного commit — отправка сообщения в Kafka.  
  4) После успешной отправки — обновление `published_to_kafka = true` в этой записи.  
  5) Ответ клиенту 201 с id записи.
- [ ] Адаптировать `EventService` (или переименовать в `OrderEventService`): метод создания записи с полями `order_id`, `user_id`, `event_type`, `event_occurred_at`, `published_to_kafka=false`; при необходимости метод обновления `published_to_kafka`.
- [ ] Эндпоинт `POST /api/v1/events`: принимать только payload событий заказов; при ошибке Kafka не возвращать 5xx по смыслу «событие не принято» — событие уже в БД, повтор публикации будет через фоновый job.

## 2.3. Интеграция с Kafka

- [ ] Добавить зависимость (например, `aiokafka` или `confluent-kafka`) и конфиг (bootstrap servers, топики).
- [ ] **Топик:** `order-events`. Ключ сообщения: составной `user_id` + `order_id` (чтобы все события одного заказа в одной партиции). Value: JSON с `event_id`, `order_id`, `user_id`, `event_type`, `event_occurred_at`.
- [ ] Реализовать отправку одного сообщения в Kafka после успешной записи в БД; при успехе — обновить `published_to_kafka = true`.
- [ ] При старте Producer: проверять существование топиков `order-events` и `order-events-dlq`; при отсутствии — создавать (например, 3 партиции для `order-events`, 1 для `order-events-dlq`). Retry подключения к Kafka при старте.

## 2.4. Фоновый job повтора публикации в Kafka

- [ ] Запуск периодической задачи вместе с приложением (например, asyncio-таск по таймеру или APScheduler).
- [ ] Выборка: записи с `published_to_kafka = false` и `created_at` в заданном окне (например, последние 24 часа), с лимитом на один проход (batch).
- [ ] Для каждой записи: сформировать сообщение как при обычной публикации, отправить в `order-events`; при успехе обновить `published_to_kafka = true`.
- [ ] Интервал job задать конфигурируемо (например, 10–30 секунд).

## 2.5. API и healthcheck

- [ ] `POST /api/v1/events` — приём одного события заказа (body = payload п. 2.1). Ответ: 201 + id записи в БД.
- [ ] `GET /api/v1/events` — список последних событий заказов из БД (для мониторинга/отладки); при необходимости пагинация.
- [ ] Убрать или заменить `GET /api/v1/events/{event_id}` при необходимости под новую модель.
- [ ] **Healthcheck:** эндпоинт `GET /health` (проверка готовности API; при необходимости — проверка доступности БД и/или Kafka). Использовать в docker-compose для `depends_on` и для event-generator.

## 2.6. Метрики (Producer)

- [ ] Эндпоинт `GET /metrics` в формате Prometheus.
- [ ] Метрики: число принятых запросов (событий) в единицу времени; число записей в БД; число сообщений, успешно отправленных в Kafka; ошибки записи в БД и ошибки Kafka (счётчики).

## 2.7. Docker и масштабирование

- [ ] Добавить сервис `producer` в `docker-compose.yml`: зависимость от `db` и `broker`; при старте — retry подключения к БД и Kafka, выполнение миграций из **`shared/db/migrations`** (например, `alembic upgrade head` в рабочей директории проекта) или отдельный шаг/init.
- [ ] Producer — **одна реплика** (один инстанс), чтобы фоновый job не дублировался.

---

# 3. Consumer

Реализуется с нуля: отдельное приложение (например, отдельная директория `consumer/` или сервис в том же репозитории).

## 3.1. Каркас приложения

- [ ] Структура проекта: точка входа, конфиг (Postgres, Kafka, топики, параметры retry/DLQ), логирование.
- [ ] Подключение к Postgres (async, тот же connection string, что и у Producer). Модели БД — из **`shared.db.schema`** (таблица `notifications` и при необходимости `events`).
- [ ] Подключение к Kafka: consumer group, подписка на топик `order-events`.

## 3.2. Обработка сообщений

- [ ] Чтение сообщений из `order-events`, десериализация JSON в модель (order_id, user_id, event_type, event_occurred_at и т.д.).
- [ ] **Идемпотентность:** ключ — пара `(order_id, event_type)`. Перед вставкой уведомления проверять наличие записи в таблице `notifications` с таким ключом. Если есть — считать обработанным, не создавать дубликат, закоммитить offset.
- [ ] Запись уведомления в таблицу `notifications`: `user_id`, `order_id`, `event_type`, `message`, `created_at`. Поле `message` — по шаблону в зависимости от `event_type` (например: «Заказ {order_id} создан», «Заказ {order_id} оплачен» и т.д.).
- [ ] Commit offset только после успешной записи в БД или после проверки «уже обработано».

## 3.3. Retry и DLQ

- [ ] При ошибке (БД, валидация и т.д.) не коммитить offset; повторить обработку с конфигурируемым числом попыток (например, 3–5) и экспоненциальным backoff.
- [ ] После исчерпания попыток: отправить сообщение в топик `order-events-dlq` (тело + метаданные: причина ошибки, число попыток, timestamp); закоммитить offset в основном топике.
- [ ] Consumer не создаёт топики; топики уже созданы Producer’ом при старте.

## 3.4. Метрики (Consumer)

- [ ] HTTP-сервер с эндпоинтом `GET /metrics` (Prometheus): число потреблённых сообщений, число созданных уведомлений, consumer lag (если доступно через клиент Kafka), время обработки одного сообщения (например, гистограмма/перцентили), число retry, число сообщений в DLQ, ошибки БД/Kafka.

## 3.5. Docker

- [ ] Сервис `consumer` в docker-compose: зависимость от `db` и `broker`; retry при старте; можно несколько реплик (одна consumer group — Kafka распределит партиции).

---

# 4. Event generator

Отдельное приложение в Docker, непрерывно генерирует события и шлёт на Producer API.

## 4.1. Логика генерации

- [ ] Настраиваемые параметры (env): базовый URL Producer API, интенсивность (событий в секунду или интервал), количество «виртуальных заказов» (order_id по кругу), вероятность дубликата, мин/макс задержки между событиями.
- [ ] Цепочки событий по заказу: `order_created` → `order_paid` → `order_shipped` → `order_delivered` или ветка `order_cancelled`; случайные задержки между шагами; с заданной вероятностью повторно отправить последнее событие (проверка идемпотентности).
- [ ] Отправка через HTTP `POST /api/v1/events` (синхронно или асинхронно); при старте — опрос health Producer (retry с backoff), затем запуск цикла генерации.

## 4.2. Развёртывание

- [ ] Отдельный сервис `event-generator` в docker-compose; `depends_on: producer` с условием `service_healthy` (healthcheck Producer).
- [ ] Параметры из `.env` (URL Producer, rate, число заказов, вероятность дубликата, задержки).
- [ ] Логирование: количество отправленных запросов, ошибок; при необходимости — отладочный вывод order_id/event_type.

---

# 5. Мониторинг (Prometheus и Grafana)

## 5.1. Prometheus

- [ ] Добавить сервис Prometheus в docker-compose.
- [ ] Конфигурация scrape: периодический сбор с `http://producer:8000/metrics` и `http://consumer:<port>/metrics` (порты согласовать с docker-compose).

## 5.2. Grafana

- [ ] Добавить сервис Grafana в docker-compose; при необходимости настроить источник данных Prometheus.
- [ ] Дашборды: throughput (события/сообщения в единицу времени), число уведомлений, consumer lag, latency обработки (p50, p95, p99), retry, DLQ, ошибки по компонентам (согласно logic.md, раздел 6).

---

# 6. Docker Compose (сводка зависимостей)

- [ ] **db** — без зависимостей; первый.
- [ ] **broker** — без зависимостей; стартует вместе с db.
- [ ] **producer** — `depends_on: [db, broker]`; healthcheck по `GET /health`; одна реплика; при старте retry к БД и Kafka, создание топиков, миграции.
- [ ] **consumer** — `depends_on: [db, broker]`; при старте retry к БД и Kafka; можно несколько реплик.
- [ ] **event-generator** — `depends_on: [producer]` с условием `service_healthy`; при старте опрос health Producer.
- [ ] **Prometheus** — `depends_on` на producer и consumer (по необходимости).
- [ ] **Grafana** — `depends_on: Prometheus`.
- [ ] Общий `env_file` для сервисов, использующих БД и Kafka.

---

# 7. Проверка и сценарии нагрузки

- [ ] Ручная проверка: отправка событий на Producer, проверка появления записей в БД и уведомлений после обработки Consumer.
- [ ] Проверка идемпотентности: дубликаты от event-generator не создают второе уведомление для той же пары (order_id, event_type).
- [ ] Нагрузочный сценарий: высокая интенсивность (например, 100–1000 событий/с) в течение нескольких минут; оценка по метрикам: стабильность Producer, consumer lag, количество retry и записей в DLQ (logic.md, п. 6.3).
