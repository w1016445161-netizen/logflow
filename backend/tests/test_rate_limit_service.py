from unittest.mock import MagicMock
import pytest


class TestRateLimit:
    def test_disabled_always_allows(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", False)
        from app.services.rate_limit_service import check_rate_limit

        result = check_rate_limit("client-a", None)
        assert result["limited"] is False
        assert result["current_count"] == 0

    def test_under_threshold_allows(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_MAX_REQUESTS", 10)

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 5
        monkeypatch.setattr("app.services.rate_limit_service.get_redis_client", lambda: mock_redis)

        from app.services.rate_limit_service import check_rate_limit
        result = check_rate_limit("client-b", None)

        assert result["limited"] is False
        assert result["current_count"] == 5
        assert result["key"].endswith("client-b")

    def test_over_threshold_limits(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_MAX_REQUESTS", 10)

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 11
        monkeypatch.setattr("app.services.rate_limit_service.get_redis_client", lambda: mock_redis)

        from app.services.rate_limit_service import check_rate_limit
        result = check_rate_limit("client-c", None)

        assert result["limited"] is True
        assert result["current_count"] == 11

    def test_first_request_sets_ttl(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", True)

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        monkeypatch.setattr("app.services.rate_limit_service.get_redis_client", lambda: mock_redis)

        from app.services.rate_limit_service import check_rate_limit
        check_rate_limit("client-d", None)

        mock_redis.expire.assert_called_once()

    def test_redis_error_degrade_allows(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", True)

        mock_redis = MagicMock()
        from redis import RedisError

        mock_redis.incr.side_effect = RedisError("connection refused")
        monkeypatch.setattr("app.services.rate_limit_service.get_redis_client", lambda: mock_redis)

        from app.services.rate_limit_service import check_rate_limit
        result = check_rate_limit("client-e", None)

        assert result["limited"] is False
        assert result["current_count"] == 0

    def test_falls_back_to_ip_when_no_client_id(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", True)

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 3
        monkeypatch.setattr("app.services.rate_limit_service.get_redis_client", lambda: mock_redis)

        from app.services.rate_limit_service import check_rate_limit
        result = check_rate_limit(None, "10.0.0.5")

        assert "ip:10.0.0.5" in result["key"]

    def test_anonymous_when_no_client_id_or_ip(self, monkeypatch):
        monkeypatch.setattr("app.services.rate_limit_service.settings.RATE_LIMIT_ENABLED", True)

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 2
        monkeypatch.setattr("app.services.rate_limit_service.get_redis_client", lambda: mock_redis)

        from app.services.rate_limit_service import check_rate_limit
        result = check_rate_limit(None, None)

        assert "anonymous" in result["key"]
