import json
from uuid import UUID

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message
from pydantic import BaseModel

from app.api.document import delete_document
from app.core.config import get_pubsub_settings, get_s3_settings
from app.db.database import get_db
from app.dependencies import get_qdrant_vector_store, get_s3_client

pubsub_settings = get_pubsub_settings()

# Set these values accordingly
PROJECT_ID = pubsub_settings.GCP_PROJECT_ID
SUBSCRIPTION = pubsub_settings.GCP_SUBSCRIPTION


class DeleteDocumentMessage(BaseModel):
    type: str
    doc_id: UUID


def callback(message: Message) -> None:
    db_gen = get_db()
    try:
        payload = json.loads(message.data.decode("utf-8"))
        parsed = DeleteDocumentMessage(**payload)

        delete_document(
            parsed.doc_id,
            next(db_gen),
            get_s3_client(),
            get_s3_settings(),
            get_qdrant_vector_store(),
        )
        message.ack()
    except Exception as e:
        print(f"Error while deleting document: {e}")
        message.nack()
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def listen_to_pubsub():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...")

    try:
        streaming_pull_future.result()  # Block indefinitely
    except KeyboardInterrupt:
        streaming_pull_future.cancel()  # Trigger graceful shutdown
        print("Stopped listening.")


if __name__ == "__main__":
    listen_to_pubsub()
