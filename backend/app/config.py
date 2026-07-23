from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "monitoring"
    db_user: str = "monitoring_user"
    db_password: str = ""

    secret_key: str = "change_me"
    access_token_expire_minutes: int = 60
    agent_api_key: str = ""

    offline_timeout_seconds: int = 60
    # How often agents report, used to compute expected check-ins for uptime %.
    agent_interval_seconds: int = 15
    # A warning must fall this many percentage points below its configured
    # threshold before its alert episode recovers. This prevents alert flapping
    # when a metric repeatedly moves just above and below the threshold.
    alert_recovery_margin_percent: float = 2.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
