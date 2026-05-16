import json
import random
import time
import uuid

from locust import HttpUser, between, task


PATHS = [
    "/api/login",
    "/api/users/profile",
    "/api/products/search",
    "/api/orders/create",
    "/api/payments/callback",
    "/api/admin/dashboard",
]

EVENT_TYPES = {
    "api_access": 0.82,
    "api_error": 0.08,
    "slow_request": 0.06,
    "auth_failed": 0.04,
}

STATUS_CODES = {
    200: 0.85,
    400: 0.05,
    401: 0.05,
    500: 0.05,
}


def _random_choice(weights: dict):
    items = list(weights.items())
    r = random.random()
    cumulative = 0.0
    for key, weight in items:
        cumulative += weight
        if r <= cumulative:
            return key
    return items[-1][0]


def _random_duration_ms() -> int:
    if random.random() < 0.05:
        return random.randint(1000, 3000)
    return random.randint(30, 300)


def _build_event_payload():
    user_id = str(uuid.uuid4())[:8]
    timestamp_ms = int(time.time() * 1000)
    return {
        "client_id": f"ingest-{user_id}-{timestamp_ms}-{random.randint(0, 9999)}",
        "user_id": f"u-{user_id}",
        "event_type": _random_choice(EVENT_TYPES),
        "path": random.choice(PATHS),
        "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "status_code": _random_choice(STATUS_CODES),
        "duration_ms": _random_duration_ms(),
        "ip": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "user_agent": "Mozilla/5.0 (Locust Ingest Only)",
        "service_name": "gateway-service",
        "trace_id": str(uuid.uuid4()),
        "extra": {"source": "locust_ingest_only", "scenario": "ingest_only"},
    }


class LogFlowIngestUser(HttpUser):
    wait_time = between(0.01, 0.03)

    @task
    def post_event(self):
        payload = _build_event_payload()
        with self.client.post(
            "/api/events",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/api/events [ingest-only]",
        ) as resp:
            if resp.status_code == 429:
                resp.failure("Unexpected 429 — random client_id should not trigger rate limit")
                return

            try:
                body = resp.json()
            except Exception:
                resp.failure("Response is not valid JSON")
                return

            if not body.get("success"):
                resp.failure(f"success=false: {body.get('message', '')}")
                return

            # sync_fallback means Kafka Producer is unavailable but request
            # was still persisted via sync fallback — not a failure for the
            # caller, but should be noted in the report as a Kafka health signal.
            write_mode = body.get("data", {}).get("write_mode", "")
            if write_mode == "sync_fallback":
                resp.request_meta["_sync_fallback"] = True
