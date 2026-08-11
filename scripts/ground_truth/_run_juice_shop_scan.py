"""One-off: run a real pipeline against juice-shop and dump findings/tasks
JSON for match_findings.py, same pattern as the dvwa sample run already
committed in this directory (audit C-09). Not part of the regular test
suite — run manually once to produce the sample files.

Reuses the create/trigger/poll/fetch/cleanup flow from
scripts/measurement_campaign.py (run_pipeline) instead of reimplementing it.

Run via: docker compose exec backend python scripts/ground_truth/_run_juice_shop_scan.py
"""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from measurement_campaign import run_pipeline  # noqa: E402


def main() -> None:
    name = f"ground-truth-juice-shop-{uuid.uuid4().hex[:8]}"
    scan_id, status, scan, tasks, findings = run_pipeline(
        name, "juice-shop", "_run_juice_shop_scan.py"
    )
    print(f"scan {scan_id} finished with status={status}")

    if status != "completed":
        print(f"FAILED: scan ended in status={status}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(__file__).parent
    (out_dir / "sample_run_juice_shop_findings.json").write_text(
        json.dumps(findings, indent=2), encoding="utf-8"
    )
    (out_dir / "sample_run_juice_shop_tasks.json").write_text(
        json.dumps(tasks, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(findings)} findings, {len(tasks)} tasks. scan_id={scan_id}")


if __name__ == "__main__":
    main()
