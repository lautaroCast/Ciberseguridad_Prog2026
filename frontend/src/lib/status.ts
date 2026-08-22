import type { ScanStatus, ScanTaskStatus } from "../types";

export type AnyStatus = ScanStatus | ScanTaskStatus;

const LABELS: Record<AnyStatus, string> = {
  pending: "pendiente",
  running: "en curso",
  completed: "completado",
  failed: "fallido",
  cancelled: "cancelado",
  skipped: "omitido",
};

export function statusLabel(status: AnyStatus): string {
  return LABELS[status] ?? status;
}

export function statusColor(status: AnyStatus): string {
  if (status === "completed") return "var(--ok)";
  if (status === "running") return "var(--accent)";
  if (status === "failed") return "var(--bad)";
  return "var(--ink-3)";
}
