from unittest.mock import MagicMock
from app.schemas.event import EventCreate


def _make_event_data():
    return EventCreate(
        client_id="test-client",
        event_type="api_access",
        path="/test",
        method="POST",
        status_code=200,
        duration_ms=10,
    )


class TestEventSubmitMode:
    def test_sync_mode_writes_to_db(self, monkeypatch):
        monkeypatch.setattr("app.services.event_service.settings.EVENT_WRITE_MODE", "sync")

        mock_db = MagicMock()
        create_called = []

        def mock_create_event(db, data, event_id, request_id):
            create_called.append(1)
            return MagicMock()

        monkeypatch.setattr("app.services.event_service.create_event", mock_create_event)

        from app.services.event_service import submit_event

        result = submit_event(mock_db, _make_event_data())

        assert len(create_called) == 1
        assert result["write_mode"] == "sync"
        assert result["event_id"]
        assert result["request_id"]

    def test_kafka_mode_success_returns_kafka_metadata(self, monkeypatch):
        monkeypatch.setattr("app.services.event_service.settings.EVENT_WRITE_MODE", "kafka")
        monkeypatch.setattr("app.services.event_service.settings.KAFKA_PRODUCER_ENABLED", True)

        create_called = []

        def mock_create_event(db, data, event_id, request_id):
            create_called.append(1)

        def mock_send_to_kafka(payload):
            return {"topic": "logflow-events", "partition": 0, "offset": 42}

        monkeypatch.setattr("app.services.event_service.create_event", mock_create_event)
        monkeypatch.setattr("app.kafka.producer.send_event_to_kafka", mock_send_to_kafka)

        from app.services.event_service import submit_event

        mock_db = MagicMock()
        result = submit_event(mock_db, _make_event_data())

        assert len(create_called) == 0
        assert result["write_mode"] == "kafka"
        assert result["kafka_topic"] == "logflow-events"
        assert result["kafka_partition"] == 0
        assert result["kafka_offset"] == 42

    def test_kafka_failure_fallback_to_sync(self, monkeypatch):
        monkeypatch.setattr("app.services.event_service.settings.EVENT_WRITE_MODE", "kafka")
        monkeypatch.setattr("app.services.event_service.settings.KAFKA_PRODUCER_ENABLED", True)

        create_called = []

        def mock_create_event(db, data, event_id, request_id):
            create_called.append(1)

        def mock_send_to_kafka(payload):
            raise RuntimeError("kafka broker down")

        monkeypatch.setattr("app.services.event_service.create_event", mock_create_event)
        monkeypatch.setattr("app.kafka.producer.send_event_to_kafka", mock_send_to_kafka)

        from app.services.event_service import submit_event

        mock_db = MagicMock()
        result = submit_event(mock_db, _make_event_data())

        assert len(create_called) == 1
        assert result["write_mode"] == "sync_fallback"
        assert "kafka broker down" in result["fallback_reason"]

    def test_kafka_producer_disabled_fallback_to_sync(self, monkeypatch):
        monkeypatch.setattr("app.services.event_service.settings.EVENT_WRITE_MODE", "kafka")
        monkeypatch.setattr("app.services.event_service.settings.KAFKA_PRODUCER_ENABLED", False)

        create_called = []

        def mock_create_event(db, data, event_id, request_id):
            create_called.append(1)

        monkeypatch.setattr("app.services.event_service.create_event", mock_create_event)

        from app.services.event_service import submit_event

        mock_db = MagicMock()
        result = submit_event(mock_db, _make_event_data())

        assert len(create_called) == 1
        assert result["write_mode"] == "sync_fallback"
        assert result["fallback_reason"] == "producer disabled"
