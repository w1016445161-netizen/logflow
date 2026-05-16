import json
import random
import uuid

from locust import HttpUser, between, task

FIXED_CLIENT_ID = "rate-limit-load-test"


class RateLimitUser(HttpUser):
    wait_time = between(0.01, 0.03)

    @task
    def post_event(self):
        payload = {
            "client_id": FIXED_CLIENT_ID,
            "user_id": str(uuid.uuid4())[:8],
            "event_type": "api_access",
            "path": "/api/login",
            "method": "POST",
            "status_code": 200,
            "duration_ms": random.randint(30, 100),
            "ip": "10.0.0.1",
            "user_agent": "Mozilla/5.0 (Rate Limit Test)",
            "service_name": "gateway-service",
            "trace_id": str(uuid.uuid4()),
            "extra": {"rate_limit_test": True},
        }

        with self.client.post(
            "/api/events",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/api/events [rate-limit-check]",
        ) as resp:
            if resp.status_code == 429:
                resp.success()
                return

            try:
                body = resp.json()
            except Exception:
                resp.failure("Response is not valid JSON")
                return

            if resp.status_code >= 400:
                resp.failure(f"Unexpected status {resp.status_code}: {body.get('message', '')}")
                return

            if not body.get("success"):
                resp.failure(f"success=false: {body.get('message', '')}")
