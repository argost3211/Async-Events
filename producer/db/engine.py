from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from producer.core.config import config

engine = create_async_engine(
    config.pg_url(),
    echo=config.debug,
    future=True,
    pool_size=30,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)
