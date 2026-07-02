"""OWASP ZAP adapter — spider + active scan, JSON via output file.

Uses ZAP's `-quickurl`/`-quickout` CLI mode (one-shot process, exits when
done) rather than driving the full ZAP API against a long-running daemon —
that keeps every adapter in this service following the same "one process
per scan" model instead of ZAP being a special case that needs its own
lifecycle management.

Confirmed by hand while building this module: a full spider + active scan
against even a small single-page app takes several minutes — that's
inherent to active scanning (ZAP actually attacks every discovered
parameter), not a bug. ZAP is expected to be the slowest tool in the
pipeline; `SCANNER_MAX_TIMEOUT_SECONDS` (900s default) is sized with that
in mind. `-quickout` infers its report format (JSON here) from the output
file's extension, hence `output_file_extension = ".json"`.
"""

import json
from typing import Any, ClassVar

from app.adapters.base import ScannerAdapter


class ZapAdapter(ScannerAdapter):
    tool_name: ClassVar[str] = "zap"
    uses_output_file: ClassVar[bool] = True
    output_file_extension: ClassVar[str] = ".json"

    def build_command(
        self, *, target: str, port: int, scheme: str, options: dict[str, Any], output_path: str
    ) -> list[str]:
        url = f"{scheme}://{target}:{port}"
        return ["zap.sh", "-cmd", "-quickurl", url, "-quickout", output_path]

    def parse_output(self, raw_output: str) -> Any:
        return json.loads(raw_output) if raw_output.strip() else None
