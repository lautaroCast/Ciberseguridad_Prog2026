from app.adapters.nmap_adapter import NmapAdapter


def test_only_open_ports_returned(nmap_xml_two_hosts):
    adapter = NmapAdapter()
    services = adapter.parse_output(nmap_xml_two_hosts)
    # 3 ports total across both hosts, only one is "open"
    assert len(services) == 1
    assert services[0]["host"] == "10.0.0.5"
    assert services[0]["port"] == 3000
    assert services[0]["service_name"] == "http"
    assert services[0]["product"] == "Node.js"
    assert services[0]["version"] == "18"


def test_no_hosts_returns_empty(nmap_xml_no_hosts):
    adapter = NmapAdapter()
    assert adapter.parse_output(nmap_xml_no_hosts) == []


def test_build_command_includes_target():
    adapter = NmapAdapter()
    command = adapter.build_command(
        target="juice-shop", port=80, scheme="http", options={}, output_path=""
    )
    assert command[-1] == "juice-shop"
    assert "-p" not in command


def test_build_command_with_custom_ports():
    adapter = NmapAdapter()
    command = adapter.build_command(
        target="juice-shop", port=80, scheme="http", options={"ports": "1-1000"}, output_path=""
    )
    assert "-p" in command
    assert "1-1000" in command
