"""Nmap adapter — reconnaissance / service-version detection, XML on stdout."""

import xml.etree.ElementTree as ET
from typing import Any, ClassVar

from app.adapters.base import ScannerAdapter


class NmapAdapter(ScannerAdapter):
    tool_name: ClassVar[str] = "nmap"

    def build_command(
        self, *, target: str, port: int, scheme: str, options: dict[str, Any], output_path: str
    ) -> list[str]:
        # nmap scans a port range, not a single URL — `port`/`scheme` (used
        # by the HTTP-oriented adapters) don't apply here. `options["ports"]`
        # overrides the default top-1000-ports scan, e.g. "1-1000" or "80,443".
        command = ["nmap", "-sV", "-T4", "-oX", "-"]
        ports = options.get("ports")
        if ports:
            command += ["-p", str(ports)]
        command.append(target)
        return command

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        """Extract open-port/service rows shaped like the `services` table."""
        root = ET.fromstring(raw_output)
        services: list[dict[str, Any]] = []
        for host in root.findall("host"):
            address_el = host.find("address")
            host_ip = address_el.get("addr") if address_el is not None else None
            for port_el in host.findall("ports/port"):
                state_el = port_el.find("state")
                if state_el is None or state_el.get("state") != "open":
                    continue
                service_el = port_el.find("service")
                services.append(
                    {
                        "host": host_ip,
                        "port": int(port_el.get("portid")),
                        "protocol": port_el.get("protocol"),
                        "service_name": service_el.get("name") if service_el is not None else None,
                        "product": service_el.get("product") if service_el is not None else None,
                        "version": service_el.get("version") if service_el is not None else None,
                    }
                )
        return services
