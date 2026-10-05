"""Regression tests for the Hailo proxy's CORS response headers."""

# pylint: disable=protected-access

import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROXY_PATH = Path(__file__).resolve().parents[1] / "hailo-sanitize-proxy.py"
PROXY_SPEC = importlib.util.spec_from_file_location("hailo_sanitize_proxy", PROXY_PATH)
if PROXY_SPEC is None or PROXY_SPEC.loader is None:
    raise ImportError("Could not load hailo-sanitize-proxy.py")

PROXY = importlib.util.module_from_spec(PROXY_SPEC)
PROXY_SPEC.loader.exec_module(PROXY)


class CorsHeaderTests(unittest.TestCase):
    """Verify request origins cannot inject response headers."""

    def test_origin_with_newline_is_rejected_even_if_configured(self) -> None:
        """Reject CR/LF even when an invalid value enters the allowlist."""
        origin = "http://localhost:8787\r\nX-Injected: yes"
        sent_headers = []
        handler = SimpleNamespace(
            _origin_header=lambda: origin,
            send_header=lambda name, value: sent_headers.append((name, value)),
        )

        with patch.object(PROXY, "CORS_ALLOWED_ORIGINS", {origin}):
            self.assertFalse(PROXY.ProxyHandler._is_origin_allowed(handler, origin))
            PROXY.ProxyHandler._send_cors_headers(handler)

        self.assertNotIn(("Access-Control-Allow-Origin", origin), sent_headers)

    def test_allowed_origin_is_emitted_from_configuration(self) -> None:
        """Preserve the CORS header for a valid configured origin."""
        origin = "http://localhost:8787"
        sent_headers = []
        handler = SimpleNamespace(
            _origin_header=lambda: origin,
            send_header=lambda name, value: sent_headers.append((name, value)),
        )

        with patch.object(PROXY, "CORS_ALLOWED_ORIGINS", {origin}):
            PROXY.ProxyHandler._send_cors_headers(handler)

        self.assertIn(("Access-Control-Allow-Origin", origin), sent_headers)


class ChatBodySanitizationTests(unittest.TestCase):
    """Verify malformed text parts do not break request sanitization."""

    def test_structured_role_does_not_crash_logging(self) -> None:
        """Untrusted roles must not become unhashable dictionary keys."""
        roles: tuple[object, ...] = ([], {}, ["user"], None, 17, False)
        for role in roles:
            with self.subTest(role=role):
                body = json.dumps({"messages": [{"role": role}]}).encode()
                self.assertIn('"unknown": 1', PROXY._summarize_request_body(body))

    def test_string_roles_are_preserved_in_summary(self) -> None:
        """Valid roles retain their original counts."""
        body = b'{"messages":[{"role":"user"},{"role":"user"},{"role":"system"}]}'
        summary = PROXY._summarize_request_body(body)
        self.assertIn('"user": 2', summary)
        self.assertIn('"system": 1', summary)

    def test_invalid_messages_container_is_emptied(self) -> None:
        """Only lists may be passed to message simplification."""
        for messages in (17, "user", {"role": "user"}, False):
            with self.subTest(messages=messages):
                body = json.dumps({"messages": messages}).encode()
                result = PROXY.sanitize_chat_body(body, tool_prompt_enabled=False)
                self.assertEqual(json.loads(result)["messages"], [])

    def test_non_string_content_is_normalized(self) -> None:
        """Malformed content cannot break prompt processing or user messages."""
        contents: tuple[object, ...] = (17, False, {"text": "hello"}, None)
        for content in contents:
            for role in ("system", "user"):
                with self.subTest(content=content, role=role):
                    body = json.dumps(
                        {"messages": [{"role": role, "content": content}]}
                    ).encode()
                    result = json.loads(
                        PROXY.sanitize_chat_body(body, tool_prompt_enabled=False)
                    )
                    self.assertIsInstance(result["messages"][0]["content"], str)
                    if role == "user":
                        expected = "" if content is None else str(content)
                        self.assertEqual(result["messages"][-1]["content"], expected)

    def test_non_string_text_part_is_converted_to_string(self) -> None:
        """Convert numeric text content before joining message parts."""
        body = b'{"messages":[{"role":"user","content":[{"type":"text","text":17}]}]}'

        sanitized = PROXY.sanitize_chat_body(body, tool_prompt_enabled=False)

        self.assertEqual(json.loads(sanitized)["messages"][-1]["content"], "17")


if __name__ == "__main__":
    unittest.main()
