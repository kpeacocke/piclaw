"""Atheris target for the Hailo proxy's untrusted request parsers."""

# pylint: disable=import-error,invalid-name,protected-access

import importlib.util
import sys
from pathlib import Path

import atheris


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys._MEIPASS)
PROXY_PATH = PROJECT_ROOT / "hailo-sanitize-proxy.py"
PROXY_SPEC = importlib.util.spec_from_file_location("hailo_sanitize_proxy", PROXY_PATH)
if PROXY_SPEC is None or PROXY_SPEC.loader is None:
    raise ImportError(f"Could not load proxy module from {PROXY_PATH}")

PROXY = importlib.util.module_from_spec(PROXY_SPEC)
PROXY_SPEC.loader.exec_module(PROXY)

for function in (
    PROXY._parse_json_dict,
    PROXY._summarize_request_body,
    PROXY._summarize_response_body,
    PROXY._extract_tool_names,
    PROXY._extract_latest_user_text,
    PROXY.sanitize_chat_body,
    PROXY.parse_tool_call,
):
    atheris.instrument_func(function)


def test_one_input(data: bytes) -> None:
    """Exercise parser paths using arbitrary request bytes."""
    parsed = PROXY._parse_json_dict(data)
    PROXY._summarize_request_body(data)
    PROXY._summarize_response_body(data)
    PROXY._extract_tool_names(data)
    latest_user_text = PROXY._extract_latest_user_text(data)
    PROXY.sanitize_chat_body(data, tool_prompt_enabled=False)

    text = data.decode("utf-8", errors="replace")
    PROXY.parse_tool_call(text)
    PROXY.parse_tool_call(latest_user_text)
    if parsed is not None:
        PROXY.parse_tool_call(str(parsed.get("content", "")))


atheris.Setup(sys.argv, test_one_input)
atheris.Fuzz()
