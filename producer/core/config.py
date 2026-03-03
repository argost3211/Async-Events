from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()


class Config(BaseSettings):
    debug: bool = False
    pg_host: str = Field(alias="POSTGRES_HOST")
    pg_port: int = Field(alias="POSTGRES_PORT")
    pg_user: str = Field(alias="POSTGRES_USER")
    pg_password: str = Field(alias="POSTGRES_PASSWORD")
    pg_db: str = Field(alias="POSTGRES_DB")

    def pg_url(self) -> str:
        return f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"


config = Config()
