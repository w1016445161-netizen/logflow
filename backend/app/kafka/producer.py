import json
from kafka import KafkaProducer
from app.core.config import settings

_producer = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False, default=str).encode("utf-8"),
            acks="all",
            retries=3,
            linger_ms=5,
        )
    return _producer


def send_event_to_kafka(event_data: dict) -> dict:
    producer = _get_producer()
    future = producer.send(settings.KAFKA_TOPIC_EVENTS, value=event_data)
    record = future.get(timeout=10)
    return {
        "topic": record.topic,
        "partition": record.partition,
        "offset": record.offset,
    }
