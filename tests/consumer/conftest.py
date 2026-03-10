from unittest.mock import AsyncMock, MagicMock

import pytest

from consumer.services.notification_service import NotificationService


@pytest.fixture
def mocked_session():
    """Мок AsyncSession без реальной БД."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.begin = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def notification_service(mocked_session) -> NotificationService:
    """NotificationService с замоканной сессией."""
    return NotificationService(mocked_session)
