from typing import Any


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, data: Any = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class RateLimitException(AppException):
    def __init__(self, data: dict):
        super().__init__(
            code="RATE_LIMITED",
            message="rate limit exceeded",
            status_code=429,
            data=data,
        )
