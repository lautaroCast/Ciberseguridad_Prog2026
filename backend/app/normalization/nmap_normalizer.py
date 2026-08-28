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
    services: list[ServiceData] = []
    for item in parsed or []:
        if item.get("host") is None or item.get("port") is None:
            continue
        try:
            port = int(item["port"])
        except (TypeError, ValueError):
            # A malformed port on one entry shouldn't drop every other real
            # service Nmap found in the same run - skip just this one.
            continue
        services.append(
            ServiceData(
                host=str(item["host"]),
                port=port,
                protocol=str(item.get("protocol") or "tcp"),
                service_name=item.get("service_name"),
                product=item.get("product"),
                version=item.get("version"),
            )
        )
    return NormalizedData(services=services)
