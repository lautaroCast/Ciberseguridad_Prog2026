import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def nmap_xml_two_hosts() -> str:
    return """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="10.0.0.5" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="3000">
        <state state="open"/>
        <service name="http" product="Node.js" version="18"/>
      </port>
      <port protocol="tcp" portid="8080">
        <state state="filtered"/>
        <service name="http-proxy"/>
      </port>
    </ports>
  </host>
  <host>
    <address addr="10.0.0.6" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="closed"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""


@pytest.fixture
def nmap_xml_no_hosts() -> str:
    return '<?xml version="1.0"?>\n<nmaprun></nmaprun>\n'
