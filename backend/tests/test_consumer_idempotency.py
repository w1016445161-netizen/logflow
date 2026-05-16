from unittest.mock import MagicMock


class TestConsumerIdempotency:
    def test_event_exists_returns_true(self, monkeypatch):
        mock_db = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_filter

        from app.services.event_service import event_exists, create_event_from_payload_if_not_exists

        assert event_exists(mock_db, "existing-event-id") is True

        result, created = create_event_from_payload_if_not_exists(mock_db, {
            "event_id": "existing-event-id",
            "client_id": "c1",
            "user_id": "u1",
            "event_type": "api_access",
            "path": "/test",
            "method": "GET",
            "status_code": 200,
            "duration_ms": 10,
            "request_id": "r1",
        })

        assert result is None
        assert created is False
        mock_db.add.assert_not_called()

    def test_event_exists_returns_false(self, monkeypatch):
        mock_db = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_filter

        from app.services.event_service import event_exists, create_event_from_payload_if_not_exists

        assert event_exists(mock_db, "new-event-id") is False

        result, created = create_event_from_payload_if_not_exists(mock_db, {
            "event_id": "new-event-id",
            "client_id": "c1",
            "user_id": "u1",
            "event_type": "api_access",
            "path": "/test",
            "method": "GET",
            "status_code": 200,
            "duration_ms": 10,
            "request_id": "r1",
        })

        assert result is not None
        assert created is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
