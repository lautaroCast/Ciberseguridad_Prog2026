import { request } from "./client";
import type { FindingRead } from "../types";

export function listFindings(scanId: string): Promise<FindingRead[]> {
  return request<FindingRead[]>(`/scans/${scanId}/findings`);
}
