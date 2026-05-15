from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LogFlow"
    APP_ENV: str = "dev"
    DATABASE_URL: str = "mysql+pymysql://logflow:logflow123@localhost:3306/logflow"
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    STATS_CACHE_TTL_SECONDS: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
