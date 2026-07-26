import { downloadUrl, request } from "./client";
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

export function downloadReportUrl(reportId: string): string {
  return downloadUrl(`/reports/${reportId}/download`);
}
