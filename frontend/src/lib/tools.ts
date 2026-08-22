import { SEVERITY_ORDER } from "./severity";
import type { FindingRead, ScanTaskRead, Severity, ToolName } from "../types";
import { TOOL_ORDER } from "../types";

interface ToolMeta {
  label: string;
  /** What the tool contributes to the pipeline, shown next to its name. */
  role: string;
  /**
   * How this tool's severity output is constrained by the platform's own
   * classification policy. Surfaced in the UI on purpose: the severity
   * distribution is partly an artifact of these rules, not only a property
   * of the target, and a chart that hides that misleads the reader.
   */
  bias: string | null;
  /** Whether the tool can produce `findings` at all. */
  producesFindings: boolean;
}

export const TOOL_META: Record<ToolName, ToolMeta> = {
  nmap: {
    label: "Nmap",
    role: "Descubrimiento de puertos y servicios",
    bias: null,
    producesFindings: false,
  },
  whatweb: {
    label: "WhatWeb",
    role: "Fingerprinting de tecnologías",
    bias: null,
    producesFindings: false,
  },
  nikto: {
    label: "Nikto",
    role: "Configuraciones inseguras",
    bias: "todos sus hallazgos se fuerzan a severidad baja",
    producesFindings: true,
  },
  nuclei: {
    label: "Nuclei",
    role: "Escaneo por plantillas",
    bias: "única fuente posible de severidad crítica",
    producesFindings: true,
  },
  zap: {
    label: "OWASP ZAP",
    role: "Spider + escaneo activo",
    bias: "su escala llega hasta alta — nunca puede reportar crítica",
    producesFindings: true,
  },
};

export function isKnownTool(name: string): name is ToolName {
  return (TOOL_ORDER as readonly string[]).includes(name);
}

export function toolLabel(name: string): string {
  return isKnownTool(name) ? TOOL_META[name].label : name;
}

export interface ToolBreakdownRow {
  tool: string;
  label: string;
  role: string;
  bias: string | null;
  producesFindings: boolean;
  task: ScanTaskRead | null;
  total: number;
  counts: Record<Severity, number>;
}

function emptyCounts(): Record<Severity, number> {
  return { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
}

/**
 * Attribute every finding to the tool that produced it.
 *
 * `Finding.scan_task_id` is the only link back to a tool name, and
 * `scan_tasks` is the only endpoint that carries it — which is why tool
 * attribution needs `GET /scans/{id}/tasks` and cannot be derived from
 * the findings list alone.
 *
 * Tools the pipeline always runs are listed even when they have no task
 * row yet, so a scan in progress shows all five slots rather than growing
 * a row at a time.
 */
export function buildToolBreakdown(
  tasks: ScanTaskRead[],
  findings: FindingRead[],
): ToolBreakdownRow[] {
  const taskById = new Map(tasks.map((task) => [task.id, task]));
  const countsByTool = new Map<string, Record<Severity, number>>();

  for (const finding of findings) {
    const task = taskById.get(finding.scan_task_id);
    if (!task) continue;
    const counts = countsByTool.get(task.tool_name) ?? emptyCounts();
    counts[finding.severity] += 1;
    countsByTool.set(task.tool_name, counts);
  }

  // Known tools first, in pipeline order, then anything unexpected the
  // backend reported (a newly registered adapter, for instance).
  const extraTools = tasks
    .map((task) => task.tool_name)
    .filter((name) => !isKnownTool(name));
  const names: string[] = [...TOOL_ORDER, ...new Set(extraTools)];

  return names.map((name) => {
    const meta = isKnownTool(name) ? TOOL_META[name] : null;
    const counts = countsByTool.get(name) ?? emptyCounts();
    const total = SEVERITY_ORDER.reduce((sum, severity) => sum + counts[severity], 0);
    return {
      tool: name,
      label: meta?.label ?? name,
      role: meta?.role ?? "Herramienta adicional",
      bias: meta?.bias ?? null,
      producesFindings: meta?.producesFindings ?? true,
      task: tasks.find((task) => task.tool_name === name) ?? null,
      total,
      counts,
    };
  });
}

/** Tool name for one finding, or null when its task is not loaded yet. */
export function findingTool(finding: FindingRead, tasks: ScanTaskRead[]): string | null {
  return tasks.find((task) => task.id === finding.scan_task_id)?.tool_name ?? null;
}
