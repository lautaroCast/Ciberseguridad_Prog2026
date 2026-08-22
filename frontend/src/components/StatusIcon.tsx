import { CheckIcon, CrossIcon, DashIcon, PendingIcon, SpinnerIcon } from "./Icon";
import { statusColor, statusLabel } from "../lib/status";
import type { AnyStatus } from "../lib/status";

/** Icon + color per status — never color alone. */
export function StatusIcon({ status, size = 14 }: { status: AnyStatus; size?: number }) {
  if (status === "completed") return <CheckIcon size={size} />;
  if (status === "running") return <SpinnerIcon size={size} />;
  if (status === "failed") return <CrossIcon size={size} />;
  if (status === "pending") return <PendingIcon size={size} />;
  return <DashIcon size={size} />;
}

export function StatusBadge({ status }: { status: AnyStatus }) {
  return (
    <span className="row" style={{ gap: 6, color: statusColor(status) }}>
      <StatusIcon status={status} size={13} />
      <span style={{ fontSize: 12, fontWeight: 500 }}>{statusLabel(status)}</span>
    </span>
  );
}
