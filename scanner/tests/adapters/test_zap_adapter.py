import json

import pytest

from app.adapters.zap_adapter import ZapAdapter


def test_build_command_includes_url_and_output_path():
    adapter = ZapAdapter()
    command = adapter.build_command(
        target="juice-shop", port=80, scheme="http", options={}, output_path="/tmp/zap.json"
    )
    assert command == ["zap.sh", "-cmd", "-quickurl", "http://juice-shop:80", "-quickout", "/tmp/zap.json"]


def test_build_command_without_auth_cookie_omits_replacer_config():
    adapter = ZapAdapter()
    command = adapter.build_command(
        target="juice-shop", port=80, scheme="http", options={}, output_path="/tmp/zap.json"
    )
    assert "-config" not in command


def test_build_command_with_auth_cookie_adds_replacer_config():
    adapter = ZapAdapter()
    command = adapter.build_command(
        target="dvwa",
        port=80,
        scheme="http",
        options={},
        output_path="/tmp/zap.json",
        auth_cookie="security=low; PHPSESSID=abc123",
    )
    assert command[:6] == ["zap.sh", "-cmd", "-quickurl", "http://dvwa:80", "-quickout", "/tmp/zap.json"]
    config_values = [command[i + 1] for i, tok in enumerate(command) if tok == "-config"]
    assert "replacer.full_list(0).matchstr=Cookie" in config_values
    assert "replacer.full_list(0).enabled=true" in config_values
    assert "replacer.full_list(0).replacement=security=low; PHPSESSID=abc123" in config_values


def test_malformed_json_raises():
    adapter = ZapAdapter()
    with pytest.raises(json.JSONDecodeError):
        adapter.parse_output('{"site": [truncated')


def test_parses_valid_json():
    adapter = ZapAdapter()
    raw = '{"site": [{"alerts": [{"name": "X", "riskcode": "2"}]}]}'
    result = adapter.parse_output(raw)
    assert result == {"site": [{"alerts": [{"name": "X", "riskcode": "2"}]}]}


def test_blank_content_returns_none():
    adapter = ZapAdapter()
    assert adapter.parse_output("") is None
    assert adapter.parse_output("   ") is None


def test_uses_output_file():
    adapter = ZapAdapter()
    assert adapter.uses_output_file is True
    assert adapter.output_file_extension == ".json"
