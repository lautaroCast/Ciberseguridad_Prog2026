import { describe, expect, it } from "vitest";

import { buildToolBreakdown } from "./tools";
import type { FindingRead, ScanTaskRead, Severity } from "../types";

function task(id: string, toolName: string): ScanTaskRead {
  return {
    id,
    scan_id: "scan-1",
    tool_name: toolName,
    status: "completed",
    command: null,
    started_at: "2026-08-21T00:00:00Z",
    finished_at: "2026-08-21T00:01:00Z",
    error_message: null,
    created_at: "2026-08-21T00:00:00Z",
  };
}

function finding(id: string, taskId: string, severity: Severity): FindingRead {
  return {
    id,
    scan_id: "scan-1",
    scan_task_id: taskId,
    service_id: null,
    title: `finding ${id}`,
    description: null,
    finding_type: "test",
    evidence: null,
    confidence: null,
    cvss_score: null,
    cvss_vector: null,
    severity,
    created_at: "2026-08-21T00:00:00Z",
    cve_references: [],
  };
}

describe("buildToolBreakdown", () => {
  it("attributes each finding to the tool that produced it", () => {
    const tasks = [task("t-nuclei", "nuclei"), task("t-zap", "zap")];
    const findings = [
      finding("f1", "t-nuclei", "critical"),
      finding("f2", "t-nuclei", "info"),
      finding("f3", "t-zap", "medium"),
    ];

    const rows = buildToolBreakdown(tasks, findings);
    const nuclei = rows.find((row) => row.tool === "nuclei")!;
    const zap = rows.find((row) => row.tool === "zap")!;

    expect(nuclei.total).toBe(2);
    expect(nuclei.counts.critical).toBe(1);
    expect(nuclei.counts.info).toBe(1);
    expect(zap.total).toBe(1);
    expect(zap.counts.medium).toBe(1);
  });

  // The five pipeline tools are shown from the start so a running scan does
  // not appear to grow a tool at a time.
  it("lists every pipeline tool even with no tasks yet", () => {
    const rows = buildToolBreakdown([], []);
    expect(rows.map((row) => row.tool)).toEqual(["nmap", "whatweb", "nikto", "nuclei", "zap"]);
    expect(rows.every((row) => row.total === 0 && row.task === null)).toBe(true);
  });

  it("carries the classification bias for the tools it constrains", () => {
    const rows = buildToolBreakdown([task("t-zap", "zap")], []);
    const zap = rows.find((row) => row.tool === "zap")!;
    const nmap = rows.find((row) => row.tool === "nmap")!;
    expect(zap.bias).toMatch(/nunca puede reportar crítica/);
    expect(nmap.bias).toBeNull();
  });

  it("keeps an unknown tool reported by the backend", () => {
    const rows = buildToolBreakdown([task("t-x", "wapiti")], [finding("f1", "t-x", "low")]);
    const extra = rows.find((row) => row.tool === "wapiti")!;
    expect(extra.total).toBe(1);
    expect(extra.label).toBe("wapiti");
  });

  it("ignores findings whose task is not in the list", () => {
    const rows = buildToolBreakdown([task("t-zap", "zap")], [finding("f1", "missing", "high")]);
    expect(rows.every((row) => row.total === 0)).toBe(true);
  });
});
