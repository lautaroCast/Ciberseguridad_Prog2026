from app.adapters.nuclei_adapter import NucleiAdapter


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
