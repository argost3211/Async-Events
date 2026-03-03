from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


from producer.core.config import config

engine = create_async_engine(url=config.pg_url(), echo=config.debug)
Session = sessionmaker(engine, class_=AsyncSession)
