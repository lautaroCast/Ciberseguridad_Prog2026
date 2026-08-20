import json

import pytest

from app.adapters.nuclei_adapter import NucleiAdapter


def test_build_command_includes_url_with_no_optional_flags():
    adapter = NucleiAdapter()
    command = adapter.build_command(
        target="juice-shop", port=80, scheme="http", options={}, output_path=""
    )
    assert command == ["nuclei", "-u", "http://juice-shop:80", "-jsonl", "-silent", "-duc"]


def test_build_command_with_severity_and_tags():
    adapter = NucleiAdapter()
    command = adapter.build_command(
        target="juice-shop",
        port=80,
        scheme="http",
        options={"severity": "high,critical", "tags": "cve"},
        output_path="",
    )
    assert "-severity" in command and command[command.index("-severity") + 1] == "high,critical"
    assert "-tags" in command and command[command.index("-tags") + 1] == "cve"


def test_build_command_without_auth_cookie_omits_header_flag():
    adapter = NucleiAdapter()
    command = adapter.build_command(
        target="dvwa", port=80, scheme="http", options={}, output_path=""
    )
    assert "-H" not in command


def test_build_command_with_auth_cookie_adds_header_flag():
    adapter = NucleiAdapter()
    command = adapter.build_command(
        target="dvwa",
        port=80,
        scheme="http",
        options={},
        output_path="",
        auth_cookie="security=low; PHPSESSID=abc123",
    )
    assert "-H" in command
    idx = command.index("-H")
    assert command[idx + 1] == "Cookie: security=low; PHPSESSID=abc123"


def test_malformed_jsonl_line_raises():
    adapter = NucleiAdapter()
    with pytest.raises(json.JSONDecodeError):
        adapter.parse_output('{"template-id": "a"}\n{"template-id": truncated')


def test_parses_multiple_jsonl_lines():
    adapter = NucleiAdapter()
    raw = (
        '{"template-id": "tech-detect", "info": {"name": "A"}}\n'
        '{"template-id": "cve-check", "info": {"name": "B"}}\n'
    )
    result = adapter.parse_output(raw)
    assert len(result) == 2
    assert result[0]["info"]["name"] == "A"
    assert result[1]["info"]["name"] == "B"


def test_blank_lines_interspersed_are_skipped():
    adapter = NucleiAdapter()
    raw = '{"template-id": "a"}\n\n   \n{"template-id": "b"}\n'
    result = adapter.parse_output(raw)
    assert len(result) == 2


def test_empty_string_returns_empty_list():
    adapter = NucleiAdapter()
    assert adapter.parse_output("") == []
    assert adapter.parse_output("   ") == []
