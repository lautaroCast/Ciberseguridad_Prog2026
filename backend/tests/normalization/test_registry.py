from app.normalization.registry import get_normalizer


def test_known_tools_return_callable():
    for tool in ("nmap", "whatweb", "nikto", "nuclei", "zap"):
        normalizer = get_normalizer(tool)
        assert callable(normalizer)


def test_unknown_tool_returns_none():
    assert get_normalizer("unknown-tool") is None
