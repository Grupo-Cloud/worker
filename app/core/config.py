from functools import lru_cache
from typing import ClassVar

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logger import get_logger

logger = get_logger(__name__)


class CoreSettings(BaseSettings):
    """Critical settings that must be defined, otherwise app crashes."""

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    JWT_SECRET_KEY: str
    JWT_REFRESH_KEY: str
    GOOGLE_API_KEY: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=(".env", ".env.dev"), extra="ignore"
    )


class S3Settings(BaseSettings):
    """Optional S3 settings. If missing, S3 operations will be disabled."""

    S3_HOST: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_SECURE: bool
    S3_TYPE: str
    S3_DOCUMENT_BUCKET: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=(".env", ".env.dev"), extra="ignore"
    )


class QdrantSettings(BaseSettings):
    """Optional Qdrant settings. If missing, Qdrant operations will be disabled."""

    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION_NAME: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=(".env", ".env.dev"), extra="ignore"
    )


class PubSubSettings(BaseSettings):
    """Pub/Sub topic subscription configuration."""

    GCP_PROJECT_ID: str
    GCP_SUBSCRIPTION: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=(".env", ".env.dev"), extra="ignore"
    )


# Load core settings (mandatory, app crashes if missing)
@lru_cache
def get_core_settings() -> CoreSettings:
    try:
        return CoreSettings.model_validate({})
    except ValidationError as e:
        logger.critical(f"❌ Missing critical environment variables: {e}")
        raise SystemExit(1)  # ❌ Hard crash


# Load s3 settings (mandatory, app crashes if missing)
@lru_cache
def get_s3_settings() -> S3Settings:
    try:
        return S3Settings.model_validate({})
    except ValidationError as e:
        logger.critical(f"❌ Missing critical environment variables for s3: {e}")
        raise SystemExit(1)  # ❌ Hard crash


@lru_cache
def get_qdrant_settings() -> QdrantSettings:
    try:
        return QdrantSettings.model_validate({})
    except ValidationError as e:
        logger.critical(f"❌ Missing critical environment variables for qdrant: {e}")
        raise SystemExit(1)  # ❌ Hard crash


# Load pubsub settings (mandatory, app crashes if missing)
@lru_cache
def get_pubsub_settings() -> PubSubSettings:
    try:
        return PubSubSettings.model_validate({})
    except ValidationError as e:
        logger.critical(f"❌ Missing critical environment variables for pubsub: {e}")
        raise SystemExit(1)  # ❌ Hard crash


_ = get_core_settings()
_ = get_s3_settings()
_ = get_qdrant_settings()
_ = get_pubsub_settings()
