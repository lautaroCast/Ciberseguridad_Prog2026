from app.adapters.whatweb_adapter import WhatWebAdapter


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
