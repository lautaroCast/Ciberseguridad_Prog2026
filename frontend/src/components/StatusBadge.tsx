import type { ScanStatus } from "../types";

export function StatusBadge({ status }: { status: ScanStatus }) {
  return <span className={`badge badge--status-${status}`}>{status.toUpperCase()}</span>;
}
