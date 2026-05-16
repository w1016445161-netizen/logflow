from unittest.mock import MagicMock


class TestCacheService:
    def test_cache_hit_returns_cached_data(self, monkeypatch):
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"cached": true}'
        monkeypatch.setattr("app.services.cache_service.get_redis_client", lambda: mock_redis)

        from app.services.cache_service import get_cached_or_compute
        compute_called = []

        result = get_cached_or_compute(
            "test:key", 30,
            lambda: compute_called.append(1) or {"computed": True},
        )

        assert result == {"cached": True}
        assert len(compute_called) == 0

    def test_cache_miss_calls_compute_and_caches(self, monkeypatch):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        monkeypatch.setattr("app.services.cache_service.get_redis_client", lambda: mock_redis)

        from app.services.cache_service import get_cached_or_compute

        result = get_cached_or_compute(
            "test:key2", 30,
            lambda: {"computed": True},
        )

        assert result == {"computed": True}
        mock_redis.setex.assert_called_once()

    def test_redis_error_degrade_computes_directly(self, monkeypatch):
        mock_redis = MagicMock()
        from redis import RedisError

        mock_redis.get.side_effect = RedisError("connection refused")
        monkeypatch.setattr("app.services.cache_service.get_redis_client", lambda: mock_redis)

        from app.services.cache_service import get_cached_or_compute

        result = get_cached_or_compute(
            "test:key3", 30,
            lambda: {"fallback": True},
        )

        assert result == {"fallback": True}
