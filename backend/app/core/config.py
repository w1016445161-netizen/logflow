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
    EVENT_WRITE_MODE: str = "sync"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVENTS: str = "logflow-events"
    KAFKA_PRODUCER_ENABLED: bool = True
    KAFKA_CONSUMER_GROUP: str = "logflow-consumer-group"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
