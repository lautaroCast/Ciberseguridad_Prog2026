"""tool_name -> normalizer function lookup.

Same plugin idea as the Scanner Service's adapter registry (Módulo 4):
adding normalization support for a new tool means adding one file here
and one line in this dict — nothing else in the ingest path changes.
"""

from collections.abc import Callable
from typing import Any

from app.normalization import (
    nikto_normalizer,
    nmap_normalizer,
    nuclei_normalizer,
    whatweb_normalizer,
    zap_normalizer,
)
from app.normalization.types import NormalizedData

_NORMALIZERS: dict[str, Callable[[Any], NormalizedData]] = {
    "nmap": nmap_normalizer.normalize,
    "whatweb": whatweb_normalizer.normalize,
    "nikto": nikto_normalizer.normalize,
    "nuclei": nuclei_normalizer.normalize,
    "zap": zap_normalizer.normalize,
}


def get_normalizer(tool_name: str) -> Callable[[Any], NormalizedData] | None:
    """Returns None for an unknown tool rather than raising.

    A `scan_task` for a tool without a normalizer (e.g. a brand-new
    adapter added to the Scanner Service before its normalizer is
    written) is still recorded — it just produces no `Finding`/`Service`/
    `Technology` rows until one is added here.
    """
    return _NORMALIZERS.get(tool_name)
