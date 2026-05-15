from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LogFlow"
    APP_ENV: str = "dev"
    DATABASE_URL: str = "mysql+pymysql://logflow:logflow123@localhost:3306/logflow"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
