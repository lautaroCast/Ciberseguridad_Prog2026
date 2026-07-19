from app.adapters.zap_adapter import ZapAdapter


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
