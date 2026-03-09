from typing import AsyncGenerator, cast

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from testcontainers.postgres import PostgresContainer
from unittest.mock import AsyncMock, MagicMock

from shared.db.schema.base import Base
from producer.services.event_service import EventService


def _truncate_all_tables(conn) -> None:
    """Синхронная обёртка: TRUNCATE всех таблиц из Base.metadata (универсально при новых таблицах)."""
    tables = [t.name for t in Base.metadata.sorted_tables]
    if tables:
        conn.execute(
            text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")
        )


def _pg_url_for_asyncpg(container: PostgresContainer) -> str:
    """URL контейнера для драйвера asyncpg."""
    url = container.get_connection_url()
    if "postgresql+asyncpg://" in url:
        return url
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL в Docker через Testcontainers"""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture
def mocked_session() -> AsyncSession:
    """Мок AsyncSession без реальной БД."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    return cast(AsyncSession, session)


@pytest.fixture
def event_service(mocked_session) -> EventService:
    """EventService с замоканной сессией."""
    return EventService(mocked_session)


@pytest.fixture(scope="session")
async def test_engine(postgres_container) -> AsyncGenerator[AsyncEngine, None]:
    """Движок для тестовой БД (PostgreSQL в контейнере Testcontainers)."""
    url = _pg_url_for_asyncpg(postgres_container)
    engine = create_async_engine(url, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def _init_test_db(test_engine):
    """Один раз за сессию создаёт схему в тестовой БД (контейнер при старте пустой, TRUNCATE не нужен)."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def db_session(test_engine, _init_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Сессия на тест; после теста все таблицы из Base.metadata очищаются (TRUNCATE)."""
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session_factory() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(_truncate_all_tables)


@pytest.fixture
async def client(db_session) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP-клиент с подменой get_session на тестовую сессию."""
    from producer.main import app
    from producer.api.v1 import events

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
        finally:
            await db_session.rollback()

    app.dependency_overrides[events.get_session] = override_get_session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
