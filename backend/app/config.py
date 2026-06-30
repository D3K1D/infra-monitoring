from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "monitoring"
    db_user: str = "monitoring_user"
    db_password: str = ""

    secret_key: str = "change_me"
    access_token_expire_minutes: int = 60

    offline_timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
