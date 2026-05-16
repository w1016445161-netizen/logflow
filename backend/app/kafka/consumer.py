import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaConsumer

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.event_service import create_event_from_payload_if_not_exists


def write_dead_letter(payload: dict, error: Exception, dead_letter_path: Path | None = None) -> None:
    if dead_letter_path is None:
        dead_letter_path = Path(__file__).resolve().parent.parent.parent / "dead_letters" / "kafka_failed_events.jsonl"

    dead_letter_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_id": payload.get("event_id", "unknown"),
        "error": f"{type(error).__name__}: {error}",
        "payload": payload,
    }

    with open(dead_letter_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


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
                    event, created = create_event_from_payload_if_not_exists(db, payload)
                    if created:
                        print(f"[CONSUMED] event_id={event_id}")
                    else:
                        print(f"[SKIPPED] duplicate event_id={event_id}")
                finally:
                    db.close()
            except Exception as exc:
                print(f"[ERROR] failed to process event_id={event_id}")
                traceback.print_exc()
                try:
                    write_dead_letter(payload, exc, None)
                except Exception:
                    pass
    except KeyboardInterrupt:
        print("\n[Consumer] shutting down...")
    finally:
        consumer.close()
        print("[Consumer] stopped")


if __name__ == "__main__":
    main()
