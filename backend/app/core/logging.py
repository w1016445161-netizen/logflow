import datetime
import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
            "method": getattr(record, "method", ""),
            "path": getattr(record, "path", ""),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "client_ip": getattr(record, "client_ip", ""),
            "error": getattr(record, "error", ""),
            "exception_type": getattr(record, "exception_type", ""),
        }
        return json.dumps(log_entry, default=str)


def setup_logging():
    logger = logging.getLogger("logflow")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str = "logflow") -> logging.Logger:
    return logging.getLogger(name)
