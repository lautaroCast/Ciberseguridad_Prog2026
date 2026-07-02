"""WhatWeb -> `technologies` rows.

WhatWeb's `--log-json` output is a list with one object per scanned URL,
each holding a `plugins` dict keyed by detected technology name. Plugin
values are free-form (most tools only report a name; some also carry a
`version` list), so this only extracts what's reliably present: the
plugin name and, when given, its first reported version string.
"""

from typing import Any

from app.normalization.types import NormalizedData, TechnologyData


def normalize(parsed: list[dict[str, Any]] | None) -> NormalizedData:
    technologies: list[TechnologyData] = []
    for entry in parsed or []:
        plugins = entry.get("plugins") or {}
        for name, details in plugins.items():
            version = None
            if isinstance(details, dict):
                version_values = details.get("version")
                if isinstance(version_values, list) and version_values:
                    version = str(version_values[0])
            technologies.append(
                TechnologyData(name=str(name)[:100], detected_by="whatweb", version=version)
            )
    return NormalizedData(technologies=technologies)
