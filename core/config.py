"""
Configuration management for FreeStack.

Layered configuration: defaults < config.yaml < environment variables < CLI args
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    """Application-level configuration."""
    name: str = "freestack"
    environment: str = "development"
    debug: bool = True
    timezone: str = "UTC"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = "postgresql+asyncpg://freestack:freestack@localhost:5432/freestack"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo: bool = False
    echo_pool: bool = False


class RedisConfig(BaseModel):
    """Redis configuration."""
    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class AuthConfig(BaseModel):
    """Authentication configuration."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    bcrypt_rounds: int = 12


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    worker_class: str = "uvicorn.workers.UvicornWorker"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])
    rate_limit: str = "100/minute"
    rate_limit_storage: str = "redis"
    request_timeout: int = 30
    max_request_size: int = 10485760
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"


class CLIConfig(BaseModel):
    """CLI configuration."""
    theme: str = "dark"
    show_progress: bool = True
    confirm_destructive: bool = True
    history_file: str = "~/.freestack_history"
    completion: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file: str = "logs/app.log"
    max_bytes: int = 10485760
    backup_count: int = 5
    encoding: str = "utf-8"
    include_timestamp: bool = True
    include_level: bool = True
    include_logger: bool = True
    include_module: bool = True
    include_function: bool = True
    include_line: bool = True

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed = {"json", "console"}
        if v not in allowed:
            raise ValueError(f"format must be one of {allowed}")
        return v


class WorkerConfig(BaseModel):
    """Background worker configuration."""
    concurrency: int = 4
    max_jobs: int = 1000
    job_timeout: int = 300
    retry_attempts: int = 3
    retry_backoff: int = 60
    dead_letter_queue: bool = True
    queues: List[str] = Field(default_factory=lambda: ["default", "high", "low"])


class SchedulerConfig(BaseModel):
    """Task scheduler configuration."""
    enabled: bool = True
    timezone: str = "UTC"
    max_instances: int = 3
    coalesce: bool = True
    misfire_grace_time: int = 30


class WebSocketConfig(BaseModel):
    """WebSocket server configuration."""
    host: str = "0.0.0.0"
    port: int = 8001
    ping_interval: int = 20
    ping_timeout: int = 10
    max_message_size: int = 1048576
    max_connections: int = 10000


class StorageConfig(BaseModel):
    """File storage configuration."""
    provider: str = "local"

    class LocalConfig(BaseModel):
        root: str = "data/uploads"
        base_url: str = "/uploads"

    class S3Config(BaseModel):
        bucket: str = ""
        region: str = "us-east-1"
        endpoint_url: str = ""
        access_key: str = ""
        secret_key: str = ""
        prefix: str = "uploads/"

    local: LocalConfig = Field(default_factory=LocalConfig)
    s3: S3Config = Field(default_factory=S3Config)


class EmailConfig(BaseModel):
    """Email configuration."""
    enabled: bool = False
    provider: str = "smtp"

    class SMTPConfig(BaseModel):
        host: str = "localhost"
        port: int = 587
        username: str = ""
        password: str = ""
        use_tls: bool = True
        use_ssl: bool = False

    smtp: SMTPConfig = Field(default_factory=SMTPConfig)
    from_address: str = "noreply@freestack.local"
    from_name: str = "FreeStack"


class WebhookConfig(BaseModel):
    """Webhook configuration."""
    enabled: bool = False
    secret: str = ""
    timeout: int = 10
    max_retries: int = 3
    retry_backoff: int = 5


class MetricsConfig(BaseModel):
    """Metrics configuration."""
    enabled: bool = True
    path: str = "/metrics"
    port: int = 9090


class TracingConfig(BaseModel):
    """Distributed tracing configuration."""
    enabled: bool = False
    service_name: str = "freestack"
    exporter: str = "otlp"
    sample_rate: float = 1.0

    class OTLPConfig(BaseModel):
        endpoint: str = "http://localhost:4317"
        headers: Dict[str, str] = Field(default_factory=dict)

    otlp: OTLPConfig = Field(default_factory=OTLPConfig)


class SecurityConfig(BaseModel):
    """Security headers configuration."""

    class HeadersConfig(BaseModel):
        x_content_type_options: str = "nosniff"
        x_frame_options: str = "DENY"
        x_xss_protection: str = "1; mode=block"
        strict_transport_security: str = "max-age=31536000; includeSubDomains"
        content_security_policy: str = "default-src 'self'"
        referrer_policy: str = "strict-origin-when-cross-origin"
        permissions_policy: str = "geolocation=(), microphone=(), camera=()"

    class CORSConfig(BaseModel):
        allow_origins: List[str] = Field(default_factory=list)
        allow_methods: List[str] = Field(default_factory=list)
        allow_headers: List[str] = Field(default_factory=list)
        allow_credentials: bool = False
        max_age: int = 600

    headers: HeadersConfig = Field(default_factory=HeadersConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)


class Settings(BaseSettings):
    """Main settings class with all configuration sections."""

    model_config = SettingsConfigDict(
        env_prefix="FREESTACK_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    auth: AuthConfig
    api: APIConfig = Field(default_factory=APIConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    worker: WorkerConfig = Field(default_factory=WorkerConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    webhooks: WebhookConfig = Field(default_factory=WebhookConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @model_validator(mode="before")
    @classmethod
    def load_yaml_config(cls, data: Any) -> Any:
        """Load configuration from YAML file if present."""
        if isinstance(data, dict):
            return data

        config_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("config/config.yaml"),
            Path("config/config.yml"),
            Path.home() / ".config" / "freestack" / "config.yaml",
        ]

        for path in config_paths:
            if path.exists():
                with open(path, "r") as f:
                    yaml_data = yaml.safe_load(f)
                    if yaml_data:
                        return yaml_data

        return data


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


def load_config_from_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two configuration dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result