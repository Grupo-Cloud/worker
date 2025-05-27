import os
import uuid
from io import BytesIO
from typing import Annotated
from uuid import UUID

from langchain_qdrant import QdrantVectorStore
from minio import Minio
from sqlalchemy.orm import Session

from app.core.config import S3Settings, get_s3_settings
from app.db.database import get_db
from app.dependencies import get_qdrant_vector_store, get_s3_client, get_user
from app.exceptions.document import DocumentNotFoundException
from app.exceptions.user import UserNotFoundException
from app.models.document import FileType
from app.models.user import User
from app.schemas.document import CreateDocument, GetDocumentDetail
from app.services.chunk import service as chunk_service
from app.services.document import service
from app.services.s3 import service as s3_service
from app.services.vector import service as vector_service


def create_document(
    user_id: UUID,
    db: Session,
    file_bytes: BytesIO,
    filename: str,
    file_extension: str,
    content_type: str | None,
    file_type: FileType,
    size: int,
    s3_client: Minio,
    s3_settings: S3Settings,
    vector_store: QdrantVectorStore,
):
    s3_location = s3_service.load_document_into_s3(
        file_bytes,
        user_id,
        filename,
        content_type,
        s3_client,
        s3_settings,
    )
    chunk_ids = vector_service.load_document_into_vector_database(
        file_bytes, file_extension, vector_store
    )
    document_id = uuid.uuid4()
    service.create_document_for_user(
        db,
        CreateDocument(
            id=document_id,
            name=filename,
            file_type=file_type,
            size=size or -1,
            s3_location=s3_location,
            user_id=user_id,
        ),
    )
    chunk_service.create_chunks_into_document(db, chunk_ids, document_id)


def delete_document(
    document_id: UUID,
    db: Session,
    s3_client: Minio,
    s3_settings: S3Settings,
    vector_store: QdrantVectorStore,
):
    try:
        document = service.get_document(db, document_id)
    except DocumentNotFoundException:
        return
    s3_service.delete_document_from_s3(document.s3_location, s3_client, s3_settings)
    vector_service.drop_chunks_from_document_id(
        [chunk.id for chunk in document.chunks], vector_store
    )
    service.drop_document(db, document_id)
