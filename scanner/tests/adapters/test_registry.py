import pytest

from app.adapters.registry import AdapterNotFoundError, get_adapter, list_tools


def test_all_five_tools_registered():
    for tool in ("nmap", "whatweb", "nikto", "nuclei", "zap"):
        adapter = get_adapter(tool)
        assert adapter.tool_name == tool


def test_unknown_tool_raises():
    with pytest.raises(AdapterNotFoundError):
        get_adapter("unknown-tool")


def test_list_tools_sorted():
    assert list_tools() == sorted(["nmap", "whatweb", "nikto", "nuclei", "zap"])
