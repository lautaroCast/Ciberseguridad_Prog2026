import json

import pytest

from app.adapters.whatweb_adapter import WhatWebAdapter


def test_build_command_includes_url_and_default_aggression():
    adapter = WhatWebAdapter()
    command = adapter.build_command(
        target="juice-shop", port=80, scheme="http", options={}, output_path=""
    )
    assert command == [
        "whatweb",
        "--log-json=-",
        "-q",
        "--color=never",
        "-a",
        "3",
        "http://juice-shop:80",
    ]


def test_build_command_with_custom_aggression():
    adapter = WhatWebAdapter()
    command = adapter.build_command(
        target="juice-shop", port=443, scheme="https", options={"aggression": 1}, output_path=""
    )
    assert command[-1] == "https://juice-shop:443"
    assert "-a" in command and command[command.index("-a") + 1] == "1"


def test_malformed_json_raises():
    adapter = WhatWebAdapter()
    with pytest.raises(json.JSONDecodeError):
        adapter.parse_output('[{"plugins": {"Express": [truncated')


def test_parses_valid_json():
    adapter = WhatWebAdapter()
    raw = '[{"plugins": {"Express": {"version": ["4.17.1"]}}}]'
    result = adapter.parse_output(raw)
    assert result == [{"plugins": {"Express": {"version": ["4.17.1"]}}}]


def test_blank_stdout_returns_empty_list():
    adapter = WhatWebAdapter()
    assert adapter.parse_output("") == []
    assert adapter.parse_output("   ") == []


def test_uses_stdout_not_output_file():
    adapter = WhatWebAdapter()
    assert adapter.uses_output_file is False
