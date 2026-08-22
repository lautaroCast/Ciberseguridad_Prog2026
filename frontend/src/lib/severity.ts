import type { Severity } from "../types";

interface SeverityMeta {
  /** 1..5 — how many steps of the rank meter are filled. */
  rank: number;
  label: string;
  /** CSS custom property base, e.g. `--sev-critical`. */
  token: string;
}

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export const SEVERITY_META: Record<Severity, SeverityMeta> = {
  critical: { rank: 5, label: "Crítica", token: "--sev-critical" },
  high: { rank: 4, label: "Alta", token: "--sev-high" },
  medium: { rank: 3, label: "Media", token: "--sev-medium" },
  low: { rank: 2, label: "Baja", token: "--sev-low" },
  info: { rank: 1, label: "Informativa", token: "--sev-info" },
};

/** Sort index — critical first. */
export function severityRank(severity: Severity): number {
  return SEVERITY_ORDER.indexOf(severity);
}

export function severityColor(severity: Severity): string {
  return `var(${SEVERITY_META[severity].token})`;
}

export function severityBackground(severity: Severity): string {
  return `var(${SEVERITY_META[severity].token}-bg)`;
}

export function severityBorder(severity: Severity): string {
  return `var(${SEVERITY_META[severity].token}-line)`;
}
