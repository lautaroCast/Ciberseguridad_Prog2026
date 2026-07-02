"""Common interface every scanner tool adapter implements.

Adding a new tool to the platform means writing one class that implements
`build_command` (and usually `parse_output`), then registering an instance
in `registry.py` — nothing else in the service changes. The shared
execution logic (subprocess timing, timeout/missing-binary handling,
stdout-vs-output-file capture) lives once in `app/services/scan_runner.py`,
not duplicated per adapter.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class ScannerAdapter(ABC):
    tool_name: ClassVar[str]

    # Most tools stream results to stdout. A few (nikto, ZAP — confirmed by
    # hand while building this module) only write a complete, valid report
    # to a file once the scan finishes; `-output -`/stdout either hangs or
    # produces nothing usable for them. Adapters that need this set
    # `uses_output_file = True`; scan_runner then pre-creates a temp path,
    # passes it into build_command, and reads *that* file as the raw output
    # instead of stdout.
    uses_output_file: ClassVar[bool] = False
    # Extension for the temp file scan_runner creates when uses_output_file
    # is set. Matters for tools (ZAP) that infer their output format from
    # the file extension rather than a separate `-Format` flag.
    output_file_extension: ClassVar[str] = ".out"

    @abstractmethod
    def build_command(
        self, *, target: str, port: int, scheme: str, options: dict[str, Any], output_path: str
    ) -> list[str]:
        """Return the argv to execute for this scan.

        `output_path` is a pre-created (but empty/absent) temp file path,
        populated only when `uses_output_file` is True; adapters that
        stream to stdout ignore it.
        """

    def parse_output(self, raw_output: str) -> Any:
        """Structure this tool's raw output. Default: no structured parse."""
        return None
