from app.adapters.nikto_adapter import NiktoAdapter


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
