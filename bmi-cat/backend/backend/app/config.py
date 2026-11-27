from pathlib import Path
from typing import Literal
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlparse


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BMI_", env_file=Path(__file__).resolve().parents[2] / ".env", env_file_encoding="utf-8", extra="ignore")
    database_url: str = "sqlite:///./bmi_cat.db"
    environment: Literal["development", "production"] = "development"
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173"]
    access_seconds: int = 900
    refresh_seconds: int = 60 * 60 * 24 * 30
    reauth_seconds: int = 300
    # Production default: local HTTP must opt in explicitly with BMI_COOKIE_SECURE=false.
    cookie_secure: bool = True
    mfa_totp_encryption_key: str = ""
    webauthn_rp_id: str = ""
    webauthn_origin: str = ""
    webauthn_android_origins: list[str] = []
    webauthn_rp_name: str = "BMICat"
    security_event_retention_days: int = 365
    reset_seconds: int = 1800
    password_breach_check_enabled: bool = True
    password_breach_api_url: str = "https://api.pwnedpasswords.com/range"
    password_breach_timeout_seconds: float = 2.0
    password_breach_cache_seconds: int = 300
    password_breach_minimum_count: int = 1
    mail_mode: Literal["local", "smtp"] = "local"
    outbox_dir: str = "outbox"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "noreply@example.com"
    google_client_id: str = ""
    api_base_url: str = "http://localhost:8000"
    android_api_base_url: str = "http://10.0.2.2:8000"
    sms_outbox_dir: str = "sms_outbox"
    sms_provider: Literal["file", "not_configured"] = "file"
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    outlook_client_id: str = ""
    outlook_client_secret: str = ""
    calendar_token_key: str = ""
    rate_limit_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = ""
    rate_limit_instances: int = 1
    trusted_proxies: list[str] = []
    rate_limits: dict[str, dict] = {"login": {"limit": 10, "window": 60, "failure_threshold": 10, "failure_window": 900, "cooldowns": [60, 300, 900]}, "mfa": {"limit": 5, "window": 60, "failure_threshold": 5, "failure_window": 900, "cooldowns": [60, 300]}, "forgot": {"limit": 3, "window": 600, "failure_threshold": 99, "failure_window": 1, "cooldowns": [60]}, "reset": {"limit": 10, "window": 600, "failure_threshold": 99, "failure_window": 1, "cooldowns": [60]}, "verification": {"limit": 3, "window": 600, "failure_threshold": 99, "failure_window": 1, "cooldowns": [60]}, "verification_confirm": {"limit": 20, "window": 600, "failure_threshold": 99, "failure_window": 1, "cooldowns": [60]}, "passkey": {"limit": 8, "window": 60, "failure_threshold": 99, "failure_window": 1, "cooldowns": [60]}, "step_up": {"limit": 5, "window": 300, "failure_threshold": 3, "failure_window": 900, "cooldowns": [60, 300]}, "refresh": {"limit": 12, "window": 60, "failure_threshold": 99, "failure_window": 1, "cooldowns": [60]}}

    @field_validator("cors_origins")
    @classmethod
    def cors_origins_must_be_specific(cls, origins: list[str]) -> list[str]:
        if not origins or "*" in origins:
            raise ValueError("CORS origins must be explicit when credentials are enabled")
        for origin in origins:
            parsed = urlparse(origin)
            if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path not in ("", "/"):
                raise ValueError("CORS origins must be explicit origins")
        return origins

    @model_validator(mode="after")
    def production_requires_secure_transport(self):
        if self.environment == "production":
            if not self.cookie_secure or self.mail_mode != "smtp":
                raise ValueError("Production requires secure cookies and SMTP mail")
            if any(urlparse(origin).scheme != "https" for origin in self.cors_origins):
                raise ValueError("Production CORS origins must use HTTPS")
            production_urls = {
                "BMI_FRONTEND_URL": self.frontend_url,
                "BMI_API_BASE_URL": self.api_base_url,
                "BMI_ANDROID_API_BASE_URL": self.android_api_base_url,
                "BMI_PASSWORD_BREACH_API_URL": self.password_breach_api_url,
            }
            insecure = [name for name, value in production_urls.items() if urlparse(value).scheme != "https"]
            if insecure:
                raise ValueError("Production URLs must use HTTPS: " + ", ".join(insecure))
            if self.rate_limit_instances > 1 and self.rate_limit_backend != "redis":
                raise ValueError("Multi-instance production rate limiting requires Redis")
            if self.sms_provider == "file":
                raise ValueError("Production SMS cannot use the file provider")
        if self.rate_limit_backend == "redis":
            parsed_redis = urlparse(self.redis_url)
            if parsed_redis.scheme not in ("redis", "rediss") or not parsed_redis.hostname:
                raise ValueError("Redis rate limiter requires a valid BMI_REDIS_URL")
        return self

    @field_validator("webauthn_origin")
    @classmethod
    def webauthn_origin_must_be_secure(cls, origin: str, info) -> str:
        if not origin:
            return origin
        parsed = urlparse(origin)
        if parsed.path not in ("", "/") or parsed.params or parsed.query or parsed.fragment:
            raise ValueError("WebAuthn origin must be an origin, not a URL path")
        if info.data.get("cookie_secure", True):
            if parsed.scheme != "https":
                raise ValueError("WebAuthn requires HTTPS in production")
        elif not (parsed.scheme == "http" and parsed.hostname == "localhost"):
            raise ValueError("HTTP WebAuthn is allowed only for explicit localhost development")
        return origin.rstrip("/")

    @field_validator("webauthn_android_origins")
    @classmethod
    def android_origins_must_be_explicit(cls, origins: list[str]) -> list[str]:
        import re
        if any(not re.fullmatch(r"android:apk-key-hash:[A-Za-z0-9_-]{43}", origin) for origin in origins):
            raise ValueError("Android WebAuthn origins must be explicit APK SHA-256 hashes")
        return origins
