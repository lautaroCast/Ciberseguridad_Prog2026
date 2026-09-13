import { CheckIcon, CrossIcon, DashIcon, PendingIcon, SpinnerIcon } from "./Icon";
import type { AnyStatus } from "../lib/status";

/** Icon + color per status — never color alone. */
export function StatusIcon({ status, size = 14 }: { status: AnyStatus; size?: number }) {
  if (status === "completed") return <CheckIcon size={size} />;
  if (status === "running") return <SpinnerIcon size={size} />;
  if (status === "failed") return <CrossIcon size={size} />;
  if (status === "pending") return <PendingIcon size={size} />;
  return <DashIcon size={size} />;
}
