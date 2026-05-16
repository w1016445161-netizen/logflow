import json
from pathlib import Path


class TestDeadLetter:
    def test_write_dead_letter_creates_file(self, tmp_path):
        from app.kafka.consumer import write_dead_letter

        dl_path = tmp_path / "kafka_failed_events.jsonl"
        payload = {
            "event_id": "evt-dead-001",
            "client_id": "c1",
            "event_type": "api_access",
        }
        error = ValueError("test write error")

        write_dead_letter(payload, error, dead_letter_path=dl_path)

        assert dl_path.exists()

        lines = dl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["event_id"] == "evt-dead-001"
        assert "ValueError" in record["error"]
        assert "test write error" in record["error"]
        assert record["payload"]["client_id"] == "c1"
        assert "timestamp" in record

    def test_write_dead_letter_appends_multiple(self, tmp_path):
        from app.kafka.consumer import write_dead_letter

        dl_path = tmp_path / "failures.jsonl"
        write_dead_letter({"event_id": "e1"}, ValueError("err1"), dead_letter_path=dl_path)
        write_dead_letter({"event_id": "e2"}, RuntimeError("err2"), dead_letter_path=dl_path)

        lines = dl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

        r1 = json.loads(lines[0])
        r2 = json.loads(lines[1])
        assert r1["event_id"] == "e1"
        assert r2["event_id"] == "e2"
