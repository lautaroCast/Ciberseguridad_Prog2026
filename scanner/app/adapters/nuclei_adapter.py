"""Nuclei adapter — template-based vulnerability scanning, JSON Lines on stdout.

Templates are downloaded once at image build time (see Dockerfile), not on
first scan — a cold `nuclei -update-templates` run takes about a minute,
which would otherwise be paid by whichever request happens to run first.
`-duc` (disable update check) keeps every scan from also phoning home to
check for template updates.
"""

import json
from typing import Any, ClassVar

from app.adapters.base import ScannerAdapter


class NucleiAdapter(ScannerAdapter):
    tool_name: ClassVar[str] = "nuclei"

    def build_command(
        self, *, target: str, port: int, scheme: str, options: dict[str, Any], output_path: str
    ) -> list[str]:
        url = f"{scheme}://{target}:{port}"
        command = ["nuclei", "-u", url, "-jsonl", "-silent", "-duc"]
        severity = options.get("severity")
        if severity:
            command += ["-severity", str(severity)]
        tags = options.get("tags")
        if tags:
            command += ["-tags", str(tags)]
        return command

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        return [json.loads(line) for line in raw_output.strip().splitlines() if line.strip()]
