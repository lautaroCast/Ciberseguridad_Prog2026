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
        command = ["nuclei", "-u", url, "-jsonl", "-silent", "-duc"]
        severity = options.get("severity")
        if severity:
            command += ["-severity", str(severity)]
        tags = options.get("tags")
        if tags:
            command += ["-tags", str(tags)]
        if auth_cookie:
            command += ["-H", f"Cookie: {auth_cookie}"]
        return command

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for line in raw_output.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                # A single truncated/corrupted JSONL line (nuclei killed
                # mid-write - OOM, an external kill signal outside this
                # process's own subprocess.run(timeout=...)) shouldn't drop
                # every other finding already reported in the same run -
                # same "one malformed entry doesn't sink the batch"
                # precedent as app.normalization.nmap_normalizer. Skip just
                # this line.
                continue
        return results
