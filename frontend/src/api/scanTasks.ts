import { request } from "./client";
import type { ScanTaskRead } from "../types";

/**
 * Per-tool progress for a scan.
 *
 * This is the only endpoint that reports what each of the five tools is
 * doing individually — the scan's own `status` collapses all of them into
 * one value, so a running scan looks identical whether nmap just started
 * or ZAP is halfway through its active scan.
 */
export function listScanTasks(scanId: string): Promise<ScanTaskRead[]> {
  return request<ScanTaskRead[]>(`/scans/${scanId}/tasks`);
}
