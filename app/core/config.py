from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    enable_docs: bool = Field(default=True, alias="ENABLE_DOCS")
    session_expire_minutes: int = Field(default=480, alias="SESSION_EXPIRE_MINUTES")
    session_cookie_name: str = Field(
        default="sis-fidel-session",
        alias="SESSION_COOKIE_NAME",
    )
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        alias="SESSION_COOKIE_SAMESITE",
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    session_touch_interval_seconds: int = Field(
        default=300,
        alias="SESSION_TOUCH_INTERVAL_SECONDS",
    )

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")
        if value == "una_clave_larga_y_segura_para_desarrollo":
            raise ValueError("SECRET_KEY no puede usar el valor inseguro por defecto")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings() # pyright: ignore[reportCallIssue]
