"""WhatWeb adapter — technology fingerprinting, JSON on stdout.

`-q --color=never` are required, not cosmetic: without them WhatWeb
interleaves its colorized human-readable report into the same stdout
stream as `--log-json=-`, corrupting the JSON (confirmed by hand while
building this module).
"""

import json
from typing import Any, ClassVar

from app.adapters.base import ScannerAdapter


class WhatWebAdapter(ScannerAdapter):
    tool_name: ClassVar[str] = "whatweb"

    def build_command(
        self, *, target: str, port: int, scheme: str, options: dict[str, Any], output_path: str
    ) -> list[str]:
        url = f"{scheme}://{target}:{port}"
        aggression = str(options.get("aggression", 3))
        return ["whatweb", "--log-json=-", "-q", "--color=never", "-a", aggression, url]

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        return json.loads(raw_output) if raw_output.strip() else []
