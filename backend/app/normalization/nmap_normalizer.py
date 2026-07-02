"""Nmap -> `services` rows.

Nmap output is reconnaissance data (open ports/service versions), not a
vulnerability by itself — it feeds the `services` table only (and, via
Módulo 6's future tool-selection stage, decides which HTTP-oriented
scanners are worth running against a target), so it never produces
`Finding` rows.
"""

from typing import Any

from app.normalization.types import NormalizedData, ServiceData


def normalize(parsed: list[dict[str, Any]] | None) -> NormalizedData:
    services = [
        ServiceData(
            host=str(item["host"]),
            port=int(item["port"]),
            protocol=str(item.get("protocol") or "tcp"),
            service_name=item.get("service_name"),
            product=item.get("product"),
            version=item.get("version"),
        )
        for item in (parsed or [])
        if item.get("host") is not None and item.get("port") is not None
    ]
    return NormalizedData(services=services)
