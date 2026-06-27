from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    db_echo: bool = False
    telegram_bot_token: str = ""
    telegram_channel_id: str = ""
    jwt_secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60 * 24
    app_base_url: str = "http://51.83.160.143:8000"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Market AI"
    smtp_use_tls: bool = True
    email_verification_expire_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
