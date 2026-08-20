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
        self,
        *,
        target: str,
        port: int,
        scheme: str,
        options: dict[str, Any],
        output_path: str,
        auth_cookie: str | None = None,
    ) -> list[str]:
        url = f"{scheme}://{target}:{port}"
        command = ["zap.sh", "-cmd", "-quickurl", url, "-quickout", output_path]
        if auth_cookie:
            # ZAP's Replacer add-on, configured via generic -config
            # key=value pairs, injects a header into every outgoing
            # request regardless of scan mode — no need to move off
            # -quickurl/-quickout to the Automation Framework just to
            # carry an authenticated session. Verified by hand against the
            # running DVWA lab.
            command += [
                "-config", "replacer.full_list(0).description=auth-cookie",
                "-config", "replacer.full_list(0).enabled=true",
                "-config", "replacer.full_list(0).matchtype=REQ_HEADER",
                "-config", "replacer.full_list(0).matchstr=Cookie",
                "-config", "replacer.full_list(0).regex=false",
                "-config", f"replacer.full_list(0).replacement={auth_cookie}",
            ]
        return command

    def parse_output(self, raw_output: str) -> Any:
        return json.loads(raw_output) if raw_output.strip() else None
