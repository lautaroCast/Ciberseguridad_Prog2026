export type ScanStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type Severity = "info" | "low" | "medium" | "high" | "critical";
export type ReportFormat = "pdf" | "html" | "markdown" | "json";

export interface TargetRead {
  id: string;
  name: string;
  host: string;
  description: string | null;
  is_lab_target: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TargetCreate {
  name: string;
  host: string;
  description?: string | null;
}

export interface TargetUpdate {
  description?: string | null;
  is_active?: boolean;
}

export interface ScanRead {
  id: string;
  target_id: string;
  status: ScanStatus;
  pipeline_run_id: string | null;
  triggered_by: string | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface ScanCreate {
  triggered_by?: string | null;
}

export interface CveReferenceRead {
  id: string;
  cve_id: string;
  cvss_score: number | null;
  cvss_vector: string | null;
  description: string | null;
  source_url: string | null;
}

export interface FindingRead {
  id: string;
  scan_id: string;
  scan_task_id: string;
  service_id: string | null;
  title: string;
  description: string | null;
  finding_type: string;
  evidence: string | null;
  confidence: string | null;
  cvss_score: number | null;
  cvss_vector: string | null;
  severity: Severity;
  created_at: string;
  cve_references: CveReferenceRead[];
}

export interface ReportRead {
  id: string;
  scan_id: string;
  format: ReportFormat;
  file_path: string;
  generated_at: string;
  generated_by: string | null;
}
