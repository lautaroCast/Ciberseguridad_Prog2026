from app.normalization import nmap_normalizer


def test_well_formed_services():
    parsed = [
        {"host": "juice-shop", "port": 3000, "service_name": "http", "product": "Node.js"},
        {"host": "juice-shop", "port": 22, "service_name": "ssh"},
    ]
    result = nmap_normalizer.normalize(parsed)
    assert len(result.services) == 2
    assert result.services[0].host == "juice-shop"
    assert result.services[0].port == 3000
    assert result.services[0].service_name == "http"
    assert result.services[0].product == "Node.js"
    assert result.services[1].protocol == "tcp"  # default


def test_missing_host_filtered_out():
    parsed = [{"port": 80}, {"host": "dvwa", "port": 80}]
    result = nmap_normalizer.normalize(parsed)
    assert len(result.services) == 1
    assert result.services[0].host == "dvwa"


def test_missing_port_filtered_out():
    parsed = [{"host": "dvwa"}, {"host": "dvwa", "port": 443}]
    result = nmap_normalizer.normalize(parsed)
    assert len(result.services) == 1
    assert result.services[0].port == 443


def test_empty_input():
    assert nmap_normalizer.normalize([]).services == []
    assert nmap_normalizer.normalize(None).services == []


def test_non_numeric_port_skipped_not_raised():
    # 8th independent evaluation: int(item["port"]) used to have no
    # try/except, unlike the sanitization pattern this project applies
    # elsewhere (severity.sanitize_cvss_score) - one malformed port used to
    # crash the whole batch instead of just being skipped.
    parsed = [{"host": "dvwa", "port": "not-a-port"}, {"host": "dvwa", "port": 80}]
    result = nmap_normalizer.normalize(parsed)
    assert len(result.services) == 1
    assert result.services[0].port == 80
