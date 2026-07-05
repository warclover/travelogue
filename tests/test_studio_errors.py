"""Studio API error payload helpers."""

from __future__ import annotations

from travelogue.demo.build import DemoError
from travelogue.errors import CodeError
from travelogue.web.studio_errors import client_error_payload, internal_error_payload, user_message


class _SampleError(CodeError):
    pass


def test_internal_error_payload_hides_exception_text() -> None:
    body = internal_error_payload()
    assert body["ok"] is False
    assert body["error"] == "E_SERVER"
    assert "traceback" not in str(body).lower()


def test_client_error_payload_code_error() -> None:
    body = client_error_payload(_SampleError("E_TIER_PATCH", "asset missing"))
    assert body == {
        "ok": False,
        "error": "E_TIER_PATCH",
        "message": "asset missing",
    }


def test_client_error_payload_demo_error() -> None:
    body = client_error_payload(DemoError("E_DEMO_TOO_FEW", "demo album too few photos"))
    assert body["ok"] is False
    assert body["error"] == "E_DEMO_TOO_FEW"


def test_client_error_payload_value_error_code() -> None:
    body = client_error_payload(ValueError("E_TEMPLATE_CONFIRM_REQUIRED"))
    assert body["error"] == "E_TEMPLATE_CONFIRM_REQUIRED"


def test_client_error_payload_generic_value_error() -> None:
    body = client_error_payload(ValueError("invalid lifecycle"))
    assert body["error"] == "E_BAD_REQUEST"
    assert "invalid lifecycle" in str(body["message"])


def test_user_message_llm_network_hides_ssl_detail() -> None:
    msg = user_message(
        "E_LLM_NETWORK",
        "E_LLM_NETWORK: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol",
    )
    assert msg == "文案生成时网络中断，请重试"
    assert "SSL" not in msg
