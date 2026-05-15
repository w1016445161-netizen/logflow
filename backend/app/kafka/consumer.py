import json
import traceback
from kafka import KafkaConsumer
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.event_service import create_event_from_payload


def main():
    consumer = KafkaConsumer(
        settings.KAFKA_TOPIC_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    print(f"[Consumer] started, listening on topic: {settings.KAFKA_TOPIC_EVENTS}")
    print("[Consumer] press Ctrl+C to stop")

    try:
        for msg in consumer:
            payload = msg.value
            event_id = payload.get("event_id", "unknown")
            try:
                db = SessionLocal()
                try:
                    create_event_from_payload(db, payload)
                    print(f"[CONSUMED] event_id={event_id}")
                finally:
                    db.close()
            except Exception:
                print(f"[ERROR] failed to process event_id={event_id}")
                traceback.print_exc()
    except KeyboardInterrupt:
        print("\n[Consumer] shutting down...")
    finally:
        consumer.close()
        print("[Consumer] stopped")


if __name__ == "__main__":
    main()
