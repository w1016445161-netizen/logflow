from typing import Any, Optional


def success_response(data: Any, request_id: str, message: str = "success") -> dict:
    return {
        "success": True,
        "code": "OK",
        "message": message,
        "data": data,
        "request_id": request_id,
    }


def error_response(code: str, message: str, request_id: str, data: Any = None) -> dict:
    return {
        "success": False,
        "code": code,
        "message": message,
        "data": data,
        "request_id": request_id,
    }
