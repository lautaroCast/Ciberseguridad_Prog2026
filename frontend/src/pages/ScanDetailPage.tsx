import { Fragment, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { createReport, downloadReport, getScan, isTerminalStatus, listFindings, listReports } from "../api";
import { ErrorBanner } from "../components/ErrorBanner";
import { SeverityBadge } from "../components/SeverityBadge";
import { Spinner } from "../components/Spinner";
import { StatusBadge } from "../components/StatusBadge";
import type { FindingRead, ReportFormat, Severity } from "../types";

const POLL_INTERVAL_MS = 2000;
const ALL_SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "info"];
const REPORT_FORMATS: ReportFormat[] = ["pdf", "html", "markdown", "json"];

type SortKey = "severity" | "cvss_score" | "title";

const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

function sortFindings(findings: FindingRead[], sortKey: SortKey, ascending: boolean): FindingRead[] {
  const sorted = [...findings].sort((a, b) => {
    if (sortKey === "severity") {
      return SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
    }
    if (sortKey === "cvss_score") {
      return (a.cvss_score ?? 0) - (b.cvss_score ?? 0);
    }
    return a.title.localeCompare(b.title);
  });
  return ascending ? sorted : sorted.reverse();
}

export function ScanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const scanId = id!;
  const queryClient = useQueryClient();

  const scanQuery = useQuery({
    queryKey: ["scan", scanId],
    queryFn: () => getScan(scanId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isTerminalStatus(status) ? false : POLL_INTERVAL_MS;
    },
  });

  const findingsQuery = useQuery({
    queryKey: ["findings", scanId],
    queryFn: () => listFindings(scanId),
    refetchInterval: () => {
      const status = scanQuery.data?.status;
      return status && isTerminalStatus(status) ? false : POLL_INTERVAL_MS;
    },
  });

  const reportsQuery = useQuery({
    queryKey: ["reports", scanId],
    queryFn: () => listReports(scanId),
  });

  const createReportMutation = useMutation({
    mutationFn: (format: ReportFormat) => createReport(scanId, format),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reports", scanId] }),
  });

  const downloadReportMutation = useMutation({
    mutationFn: (reportId: string) => downloadReport(reportId),
  });

  const [severityFilter, setSeverityFilter] = useState<Set<Severity>>(new Set(ALL_SEVERITIES));
  const [sortKey, setSortKey] = useState<SortKey>("severity");
  const [ascending, setAscending] = useState(true);
  const [expandedFindingId, setExpandedFindingId] = useState<string | null>(null);

  const visibleFindings = useMemo(() => {
    const findings = findingsQuery.data ?? [];
    const filtered = findings.filter((f) => severityFilter.has(f.severity));
    return sortFindings(filtered, sortKey, ascending);
  }, [findingsQuery.data, severityFilter, sortKey, ascending]);

  function toggleSeverity(severity: Severity) {
    setSeverityFilter((prev) => {
      const next = new Set(prev);
      if (next.has(severity)) {
        next.delete(severity);
      } else {
        next.add(severity);
      }
      return next;
    });
  }

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setAscending((prev) => !prev);
    } else {
      setSortKey(key);
      setAscending(true);
    }
  }

  if (scanQuery.isLoading) return <Spinner />;
  if (scanQuery.error) return <ErrorBanner error={scanQuery.error} />;
  const scan = scanQuery.data;
  if (!scan) return null;

  return (
    <div>
      <p>
        <Link to={`/targets/${scan.target_id}`}>&larr; Volver al target</Link>
      </p>
      <h1>
        Scan <StatusBadge status={scan.status} />
      </h1>
      {scan.error_message && <div className="error-banner">{scan.error_message}</div>}

      <h2>Findings</h2>
      <div className="severity-filters">
        {ALL_SEVERITIES.map((severity) => (
          <label key={severity} className="severity-filters__item">
            <input
              type="checkbox"
              checked={severityFilter.has(severity)}
              onChange={() => toggleSeverity(severity)}
            />
            <SeverityBadge severity={severity} />
          </label>
        ))}
      </div>

      <ErrorBanner error={findingsQuery.error} />
      {findingsQuery.isLoading && <Spinner />}
      {findingsQuery.data && (
        <table className="findings-table">
          <thead>
            <tr>
              <th onClick={() => toggleSort("severity")}>Severidad</th>
              <th onClick={() => toggleSort("title")}>Título</th>
              <th>Tipo</th>
              <th onClick={() => toggleSort("cvss_score")}>CVSS</th>
              <th>CVE</th>
            </tr>
          </thead>
          <tbody>
            {visibleFindings.map((finding) => {
              const isExpanded = expandedFindingId === finding.id;
              const hasDetail = Boolean(finding.description || finding.evidence);
              return (
                <Fragment key={finding.id}>
                  <tr
                    className={hasDetail ? "findings-table__row--expandable" : undefined}
                    onClick={() =>
                      hasDetail && setExpandedFindingId(isExpanded ? null : finding.id)
                    }
                  >
                    <td>
                      <SeverityBadge severity={finding.severity} />
                    </td>
                    <td>
                      {finding.title}
                      {hasDetail && <span className="findings-table__expand-hint">{isExpanded ? " ▲" : " ▼"}</span>}
                    </td>
                    <td>{finding.finding_type}</td>
                    <td>{finding.cvss_score ?? "-"}</td>
                    <td>{finding.cve_references.map((cve) => cve.cve_id).join(", ") || "-"}</td>
                  </tr>
                  {isExpanded && (
                    <tr className="findings-table__detail-row">
                      <td colSpan={5}>
                        {finding.description && (
                          <p>
                            <strong>Descripción:</strong> {finding.description}
                          </p>
                        )}
                        {finding.evidence && (
                          <p>
                            <strong>Evidencia:</strong> {finding.evidence}
                          </p>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {visibleFindings.length === 0 && (
              <tr>
                <td colSpan={5}>Sin findings para los filtros seleccionados.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <h2>Reportes</h2>
      <div className="report-buttons">
        {REPORT_FORMATS.map((format) => (
          <button
            key={format}
            type="button"
            onClick={() => createReportMutation.mutate(format)}
            disabled={createReportMutation.isPending}
          >
            Generar {format.toUpperCase()}
          </button>
        ))}
      </div>
      <ErrorBanner error={createReportMutation.error} />

      <ErrorBanner error={reportsQuery.error} />
      <ErrorBanner error={downloadReportMutation.error} />
      {reportsQuery.data && reportsQuery.data.length > 0 && (
        <ul className="report-list">
          {reportsQuery.data.map((report) => (
            <li key={report.id}>
              <button
                type="button"
                className="report-list__download"
                onClick={() => downloadReportMutation.mutate(report.id)}
                disabled={downloadReportMutation.isPending}
              >
                {report.format.toUpperCase()} — {new Date(report.generated_at).toLocaleString()}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
