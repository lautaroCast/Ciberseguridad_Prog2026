import json

import pytest

from app.adapters.nikto_adapter import NiktoAdapter


def test_build_command_includes_url_and_default_maxtime():
    adapter = NiktoAdapter()
    command = adapter.build_command(
        target="dvwa", port=80, scheme="http", options={}, output_path="/tmp/out.json"
    )
    assert "-h" in command and command[command.index("-h") + 1] == "http://dvwa:80"
    assert "-output" in command and command[command.index("-output") + 1] == "/tmp/out.json"
    assert "-maxtime" in command and command[command.index("-maxtime") + 1] == "120s"


def test_build_command_with_custom_maxtime():
    adapter = NiktoAdapter()
    command = adapter.build_command(
        target="dvwa", port=80, scheme="http", options={"max_time": "30s"}, output_path=""
    )
    assert command[command.index("-maxtime") + 1] == "30s"


def test_build_command_without_auth_cookie_omits_add_header():
    adapter = NiktoAdapter()
    command = adapter.build_command(
        target="dvwa", port=80, scheme="http", options={}, output_path="/tmp/out.json"
    )
    assert "-Add-header" not in command


def test_build_command_with_auth_cookie_adds_cookie_header():
    adapter = NiktoAdapter()
    command = adapter.build_command(
        target="dvwa",
        port=80,
        scheme="http",
        options={},
        output_path="/tmp/out.json",
        auth_cookie="security=low; PHPSESSID=abc123",
    )
    assert "-Add-header" in command
    idx = command.index("-Add-header")
    assert command[idx + 1] == "Cookie: security=low; PHPSESSID=abc123"


def test_malformed_json_raises():
    adapter = NiktoAdapter()
    with pytest.raises(json.JSONDecodeError):
        adapter.parse_output('[{"vulnerabilities": [truncated')


def test_parses_valid_json():
    adapter = NiktoAdapter()
    raw = '[{"vulnerabilities": [{"msg": "test finding"}]}]'
    result = adapter.parse_output(raw)
    assert result == [{"vulnerabilities": [{"msg": "test finding"}]}]


def test_empty_string_returns_none():
    adapter = NiktoAdapter()
    assert adapter.parse_output("") is None
    assert adapter.parse_output("   ") is None


def test_uses_output_file():
    adapter = NiktoAdapter()
    assert adapter.uses_output_file is True
    assert adapter.output_file_extension == ".json"
