from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from consumer.core.config import config

engine = create_async_engine(
    config.pg_url(),
    echo=config.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)
