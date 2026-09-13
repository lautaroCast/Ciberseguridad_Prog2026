import { request } from "./client";
import type { ScanRead } from "../types";

export function listScansForTarget(targetId: string): Promise<ScanRead[]> {
  return request<ScanRead[]>(`/targets/${targetId}/scans`);
}

export function triggerPipeline(targetId: string): Promise<ScanRead> {
  return request<ScanRead>(`/targets/${targetId}/pipeline`, { method: "POST" });
}

export function getScan(id: string): Promise<ScanRead> {
  return request<ScanRead>(`/scans/${id}`);
}

export function isTerminalStatus(status: ScanRead["status"]): boolean {
  return status === "completed" || status === "failed" || status === "cancelled";
}
