import { downloadFile, request, triggerDownload } from "./client";
import type { ReportFormat, ReportRead } from "../types";

export function createReport(scanId: string, format: ReportFormat): Promise<ReportRead> {
  return request<ReportRead>(`/scans/${scanId}/reports`, {
    method: "POST",
    query: { format },
  });
}

export function listReports(scanId: string): Promise<ReportRead[]> {
  return request<ReportRead[]>(`/scans/${scanId}/reports`);
}

export async function downloadReport(reportId: string): Promise<void> {
  const { blob, filename } = await downloadFile(`/reports/${reportId}/download`);
  triggerDownload(blob, filename);
}
