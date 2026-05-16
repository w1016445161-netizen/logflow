from app.core.response import success_response, error_response


class TestSuccessResponse:
    def test_success_has_required_fields(self):
        result = success_response(data={"key": "val"}, request_id="req-1")
        assert result["success"] is True
        assert result["code"] == "OK"
        assert result["message"] == "success"
        assert result["data"] == {"key": "val"}
        assert result["request_id"] == "req-1"

    def test_success_custom_message(self):
        result = success_response(data=None, request_id="r2", message="created")
        assert result["message"] == "created"


class TestErrorResponse:
    def test_error_has_required_fields(self):
        result = error_response(code="NOT_FOUND", message="gone", request_id="r3", data=None)
        assert result["success"] is False
        assert result["code"] == "NOT_FOUND"
        assert result["message"] == "gone"
        assert result["data"] is None
        assert result["request_id"] == "r3"

    def test_error_with_data(self):
        result = error_response(code="RATE_LIMITED", message="too many", request_id="r4", data={"limit": 10})
        assert result["data"] == {"limit": 10}
