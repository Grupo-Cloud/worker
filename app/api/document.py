from uuid import UUID

from langchain_qdrant import QdrantVectorStore
from minio import Minio
from sqlalchemy.orm import Session

from app.core.config import S3Settings
from app.exceptions.document import DocumentNotFoundException
from app.services.document import service
from app.services.s3 import service as s3_service
from app.services.vector import service as vector_service


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
