"""Nikto adapter — web server misconfiguration checks, JSON via output file.

`-output -` does not stream valid JSON to stdout — confirmed by hand while
building this module (it hangs producing nothing until killed). Nikto only
writes a complete report once the scan finishes, so this adapter uses the
shared output-file mechanism (`uses_output_file`) instead of stdout capture.

`-maxtime` bounds the scan: nikto's full test suite (thousands of checks)
can otherwise run far longer than is useful for a lab-sized target.
"""

import json
from typing import Any, ClassVar

from app.adapters.base import ScannerAdapter


class NiktoAdapter(ScannerAdapter):
    tool_name: ClassVar[str] = "nikto"
    uses_output_file: ClassVar[bool] = True
    output_file_extension: ClassVar[str] = ".json"

    def build_command(
        self, *, target: str, port: int, scheme: str, options: dict[str, Any], output_path: str
    ) -> list[str]:
        url = f"{scheme}://{target}:{port}"
        max_time = str(options.get("max_time", "120s"))
        return [
            "perl",
            "/opt/nikto/program/nikto.pl",
            "-h",
            url,
            "-Format",
            "json",
            "-output",
            output_path,
            "-nointeractive",
            "-maxtime",
            max_time,
        ]

    def parse_output(self, raw_output: str) -> Any:
        return json.loads(raw_output) if raw_output.strip() else None
