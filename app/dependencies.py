from functools import lru_cache
from typing import Annotated

from jwt import InvalidTokenError
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from minio import Minio
from pydantic import SecretStr
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from app.core.config import get_core_settings, get_qdrant_settings, get_s3_settings
from app.core.logger import get_logger
from app.db.database import get_db
from app.exceptions.user import UserNotFoundException
from app.models.user import User
from app.services.auth import service as auth_service

logger = get_logger(__name__)


@lru_cache
def get_s3_client() -> Minio:
    settings = get_s3_settings()

    if not settings:
        logger.warning("⚠️ S3 is disabled due to missing configuration.")
        raise RuntimeError("S3 is disabled.")

    return Minio(
        endpoint=settings.S3_HOST,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        secure=settings.S3_SECURE,
    )


@lru_cache
def get_qdrant_client() -> QdrantClient:
    settings = get_qdrant_settings()

    if not settings:
        logger.warning("⚠️ Qdrant is disabled due to missing configuration.")
        raise RuntimeError("Qdrant is disabled.")

    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )


@lru_cache
def get_qdrant_vector_store() -> QdrantVectorStore:
    settings = get_qdrant_settings()
    gooogle_api_key = get_core_settings().GOOGLE_API_KEY

    if not settings:
        logger.warning(
            "⚠️ Qdrant Vector Store is disabled due to missing configuration."
        )
        raise RuntimeError("Qdrant Vector Store is disabled.")

    if not gooogle_api_key:
        logger.warning("⚠️ Google API Key is disabled due to missing configuration.")
        raise RuntimeError(
            "Google API Key is disabled for Google Generative AI Embeddings."
        )

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", google_api_key=SecretStr(gooogle_api_key)
    )

    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )
    return vector_store
