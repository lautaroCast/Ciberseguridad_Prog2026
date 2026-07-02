"""Adapter registry — the plugin seam for the whole service.

Adding a new scanning tool later means: write an adapter class (implements
`ScannerAdapter`), add one line here. `app/routers/scans.py` is generic
over `tool_name` and never needs to change.
"""

from app.adapters.base import ScannerAdapter
from app.adapters.nikto_adapter import NiktoAdapter
from app.adapters.nmap_adapter import NmapAdapter
from app.adapters.nuclei_adapter import NucleiAdapter
from app.adapters.whatweb_adapter import WhatWebAdapter
from app.adapters.zap_adapter import ZapAdapter


class AdapterNotFoundError(Exception):
    """Raised when a `tool_name` has no registered adapter."""


_ADAPTERS: dict[str, ScannerAdapter] = {
    adapter.tool_name: adapter
    for adapter in (
        NmapAdapter(),
        WhatWebAdapter(),
        NiktoAdapter(),
        NucleiAdapter(),
        ZapAdapter(),
    )
}


def get_adapter(tool_name: str) -> ScannerAdapter:
    adapter = _ADAPTERS.get(tool_name)
    if adapter is None:
        raise AdapterNotFoundError(tool_name)
    return adapter


def list_tools() -> list[str]:
    return sorted(_ADAPTERS)
