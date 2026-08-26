import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import {
  createReport,
  downloadReport,
  getScan,
  isTerminalStatus,
  listFindings,
  listReports,
  listScanTasks,
} from "../api";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import {
  AlertIcon,
  CheckIcon,
  DownloadIcon,
  FileIcon,
  SpinnerIcon,
} from "../components/Icon";
import { Crumbs } from "../components/Layout";
import { SeverityMeter } from "../components/SeverityMeter";
import { TableSkeleton } from "../components/Skeleton";
import { ToolBreakdown } from "../components/ToolBreakdown";
import { ToolErrors, ToolTimeline } from "../components/ToolTimeline";
import { elapsedSeconds, formatDateTime, formatDuration } from "../lib/format";
import { SEVERITY_META, SEVERITY_ORDER, severityColor } from "../lib/severity";
import { buildToolBreakdown, toolLabel } from "../lib/tools";
import type { FindingRead, ReportFormat, ReportRead, ScanStatus, Severity } from "../types";

type SortKey = "severity" | "title" | "type" | "origin" | "cvss";
type SortDirection = "asc" | "desc";

const POLL_INTERVAL_MS = 2000;
const REPORT_FORMATS: ReportFormat[] = ["pdf", "html", "markdown", "json"];

/**
 * Info findings are hidden by default.
 *
 * A typical run produces ~21 info findings out of ~32 — showing them by
 * default buries the handful that need action. The count of what is
 * hidden stays visible so this never reads as "that is all there is".
 */
const DEFAULT_SEVERITIES: Severity[] = ["critical", "high", "medium", "low"];

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

  const scan = scanQuery.data;
  const running = scan ? !isTerminalStatus(scan.status) : false;
  const pollWhileRunning = running ? POLL_INTERVAL_MS : (false as const);

  const tasksQuery = useQuery({
    queryKey: ["scan-tasks", scanId],
    queryFn: () => listScanTasks(scanId),
    refetchInterval: pollWhileRunning,
  });

  const findingsQuery = useQuery({
    queryKey: ["findings", scanId],
    queryFn: () => listFindings(scanId),
    refetchInterval: pollWhileRunning,
  });

  const reportsQuery = useQuery({
    queryKey: ["reports", scanId],
    queryFn: () => listReports(scanId),
    enabled: !running,
  });

  // `pollWhileRunning` flipping to `false` only stops *future* polling of
  // tasksQuery/findingsQuery — unlike reportsQuery's `enabled: !running`,
  // it doesn't force one more fetch on the transition itself, so up to
  // POLL_INTERVAL_MS of tail data (the last tool/finding written right at
  // completion) could be missing from what the UI already calls "the
  // complete list". Force exactly one refetch on the true->false edge.
  const wasRunningRef = useRef(running);
  useEffect(() => {
    if (wasRunningRef.current && !running) {
      queryClient.invalidateQueries({ queryKey: ["scan-tasks", scanId] });
      queryClient.invalidateQueries({ queryKey: ["findings", scanId] });
    }
    wasRunningRef.current = running;
  }, [running, queryClient, scanId]);

  const createReportMutation = useMutation({
    mutationFn: (format: ReportFormat) => createReport(scanId, format),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reports", scanId] }),
  });

  const [selectedSeverities, setSelectedSeverities] = useState<Set<Severity>>(
    () => new Set(DEFAULT_SEVERITIES),
  );
  const [excludedTools, setExcludedTools] = useState<Set<string>>(() => new Set());
  const [openFindingId, setOpenFindingId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("severity");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Live clock while the pipeline runs; `finished_at` is null until it ends.
  const [, forceTick] = useState(0);
  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => forceTick((n) => n + 1), 1000);
    return () => clearInterval(timer);
  }, [running]);

  const tasks = useMemo(() => tasksQuery.data ?? [], [tasksQuery.data]);
  const findings = useMemo(() => findingsQuery.data ?? [], [findingsQuery.data]);
  const breakdown = useMemo(() => buildToolBreakdown(tasks, findings), [tasks, findings]);

  const toolByTaskId = useMemo(
    () => new Map(tasks.map((task) => [task.id, task.tool_name])),
    [tasks],
  );

  const severityCounts = useMemo(() => {
    const counts: Record<Severity, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      info: 0,
    };
    for (const finding of findings) counts[finding.severity] += 1;
    return counts;
  }, [findings]);

  const toolsWithFindings = useMemo(
    () => breakdown.filter((row) => row.total > 0),
    [breakdown],
  );

  const compareFindings = useMemo(() => {
    // Nulls (missing CVSS, or a finding whose tool isn't loaded yet) always
    // sort last, regardless of direction — an unknown value isn't "low".
    function keyValue(finding: FindingRead, key: SortKey): string | number {
      switch (key) {
        case "severity":
          return SEVERITY_ORDER.indexOf(finding.severity);
        case "title":
          return finding.title.toLowerCase();
        case "type":
          return finding.finding_type.toLowerCase();
        case "origin": {
          const tool = toolByTaskId.get(finding.scan_task_id);
          return tool ? toolLabel(tool).toLowerCase() : "";
        }
        case "cvss":
          return finding.cvss_score ?? Number.NEGATIVE_INFINITY;
      }
    }

    return (a: FindingRead, b: FindingRead) => {
      const aMissing = sortKey === "cvss" ? a.cvss_score === null : false;
      const bMissing = sortKey === "cvss" ? b.cvss_score === null : false;
      if (aMissing !== bMissing) return aMissing ? 1 : -1;

      const va = keyValue(a, sortKey);
      const vb = keyValue(b, sortKey);
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sortDirection === "asc" ? cmp : -cmp;
    };
  }, [sortKey, sortDirection, toolByTaskId]);

  const visibleFindings = useMemo(() => {
    return findings
      .filter((finding) => selectedSeverities.has(finding.severity))
      .filter((finding) => {
        const tool = toolByTaskId.get(finding.scan_task_id);
        return !tool || !excludedTools.has(tool);
      })
      .sort(compareFindings);
  }, [findings, selectedSeverities, excludedTools, toolByTaskId, compareFindings]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  }

  function toggleSeverity(severity: Severity) {
    setSelectedSeverities((prev) => {
      const next = new Set(prev);
      if (next.has(severity)) next.delete(severity);
      else next.add(severity);
      return next;
    });
    setOpenFindingId(null);
  }

  function toggleTool(tool: string) {
    setExcludedTools((prev) => {
      const next = new Set(prev);
      if (next.has(tool)) next.delete(tool);
      else next.add(tool);
      return next;
    });
    setOpenFindingId(null);
  }

  if (scanQuery.isLoading) return <TableSkeleton rows={5} />;
  if (!scan) {
    // Never fetched successfully at all (as opposed to a later background
    // poll failing) — there's no cached scan to render around, so a full-page
    // error is correct here. See the inline ErrorBanner below for the
    // "already had data, a later poll failed" case.
    if (scanQuery.error) return <ErrorBanner error={scanQuery.error} />;
    return null;
  }

  const elapsed = elapsedSeconds(scan.started_at ?? scan.created_at, scan.finished_at);
  const toolCount = breakdown.length;
  const completedTools = breakdown.filter((row) => row.task?.status === "completed").length;
  const failedTools = breakdown.filter((row) => row.task?.status === "failed");
  const hiddenCount = findings.length - visibleFindings.length;
  const stalled = running && (elapsed ?? 0) > 600;

  return (
    <div>
      <Crumbs
        items={[
          { label: "Objetivos", to: "/targets" },
          { label: "Objetivo", to: `/targets/${scan.target_id}` },
          { label: "Escaneo" },
        ]}
      />

      <div className="row" style={{ gap: 16, alignItems: "flex-start", marginBottom: 20 }}>
        <div style={{ flexGrow: 1 }}>
          <h1 style={{ marginBottom: 5 }}>{running ? "Escaneo en curso" : "Hallazgos"}</h1>
          <div className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>
            scan {scan.id} · {formatDateTime(scan.created_at)}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            className="mono"
            style={{ fontSize: 26, fontWeight: 500, letterSpacing: "-0.02em", lineHeight: 1 }}
          >
            {elapsed === null ? "—" : formatDuration(elapsed)}
          </div>
          <div className="th" style={{ marginTop: 5 }}>
            {running ? "transcurrido" : "duración"}
          </div>
        </div>
      </div>

      <ErrorBanner error={scanQuery.error} />

      <ScanBanner
        running={running}
        stalled={stalled}
        status={scan.status}
        errorMessage={scan.error_message}
        completedTools={completedTools}
        toolCount={toolCount}
        failedTools={failedTools.map((row) => row.label)}
      />

      <div className="th" style={{ marginBottom: 12 }}>
        Herramientas · ejecución secuencial
      </div>
      <ErrorBanner error={tasksQuery.error} />
      {tasksQuery.isLoading ? (
        <TableSkeleton rows={5} />
      ) : (
        <ToolTimeline rows={breakdown} />
      )}
      <ToolErrors rows={breakdown} />

      {!running && findings.length > 0 && (
        <>
          <div className="th" style={{ margin: "26px 0 11px" }}>
            Aporte por herramienta
          </div>
          <ToolBreakdown rows={breakdown} />
        </>
      )}

      <div style={{ marginTop: running ? 26 : 0 }}>
        <div className="row" style={{ gap: 26, alignItems: "flex-start", flexWrap: "wrap", marginBottom: 16 }}>
          <div>
            <div className="th" style={{ marginBottom: 9 }}>
              Severidad
            </div>
            <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
              {SEVERITY_ORDER.map((severity) => (
                <button
                  key={severity}
                  type="button"
                  className="chip"
                  aria-pressed={selectedSeverities.has(severity)}
                  onClick={() => toggleSeverity(severity)}
                >
                  <SeverityMeter severity={severity} />
                  <span
                    style={{
                      color: selectedSeverities.has(severity)
                        ? severityColor(severity)
                        : "var(--ink-3)",
                    }}
                  >
                    {SEVERITY_META[severity].label}
                  </span>
                  <span className="chip__count">{severityCounts[severity]}</span>
                </button>
              ))}
            </div>
          </div>

          {toolsWithFindings.length > 0 && (
            <div>
              <div className="th" style={{ marginBottom: 9 }}>
                Herramienta
              </div>
              <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                {toolsWithFindings.map((row) => (
                  <button
                    key={row.tool}
                    type="button"
                    className="chip"
                    aria-pressed={!excludedTools.has(row.tool)}
                    onClick={() => toggleTool(row.tool)}
                  >
                    <span className="mono">{row.tool}</span>
                    <span className="chip__count">{row.total}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="row" style={{ gap: 9, alignItems: "baseline", marginBottom: 10 }}>
          <span className="mono" style={{ fontSize: 13, fontWeight: 500 }}>
            {visibleFindings.length} de {findings.length}
          </span>
          <span
            style={{
              fontSize: 12,
              color: running ? "var(--warn)" : "var(--ink-3)",
              fontStyle: running ? "italic" : "normal",
            }}
          >
            {running
              ? `lista incompleta — faltan ${toolCount - completedTools} de ${toolCount} herramientas`
              : hiddenCount > 0
                ? `${hiddenCount} ocultos por los filtros`
                : "lista completa"}
          </span>
        </div>

        <ErrorBanner error={findingsQuery.error} />

        {findingsQuery.isLoading ? (
          <TableSkeleton />
        ) : (
          <FindingsTable
            findings={visibleFindings}
            total={findings.length}
            toolCount={toolCount}
            running={running}
            failedToLoad={Boolean(findingsQuery.error)}
            openId={openFindingId}
            onToggle={(findingId) =>
              setOpenFindingId((current) => (current === findingId ? null : findingId))
            }
            toolFor={(finding) => toolByTaskId.get(finding.scan_task_id) ?? null}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={toggleSort}
          />
        )}
      </div>

      {!running && (
        <>
          <div className="th" style={{ margin: "32px 0 11px" }}>
            Reportes
          </div>
          <div className="panel" style={{ padding: "16px 18px" }}>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
              {REPORT_FORMATS.map((format) => (
                <button
                  key={format}
                  type="button"
                  className="btn"
                  onClick={() => createReportMutation.mutate(format)}
                  disabled={createReportMutation.isPending}
                >
                  {createReportMutation.isPending &&
                  createReportMutation.variables === format ? (
                    <SpinnerIcon size={12} />
                  ) : (
                    <FileIcon />
                  )}
                  Generar {format.toUpperCase()}
                </button>
              ))}
            </div>

            <ErrorBanner error={createReportMutation.error} />
            <ErrorBanner error={reportsQuery.error} />

            {reportsQuery.data && reportsQuery.data.length === 0 && (
              <p style={{ margin: 0, fontSize: 12, color: "var(--ink-3)" }}>
                Todavía no se generó ningún reporte para este escaneo.
              </p>
            )}

            {reportsQuery.data && reportsQuery.data.length > 0 && (
              <div style={{ borderTop: "1px solid var(--line)" }}>
                {reportsQuery.data.map((report) => (
                  <ReportRow key={report.id} report={report} />
                ))}
              </div>
            )}

            <p style={{ margin: "12px 0 0", fontSize: 11, color: "var(--ink-3)" }}>
              La descarga usa la clave de API, así que no es un enlace directo: el dashboard pide
              el archivo y lo entrega al navegador.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

function ReportRow({ report }: { report: ReportRead }) {
  // One useMutation instance per row, not one shared across all reports —
  // a single shared mutation identified "is this row downloading/errored"
  // by comparing `.variables` to `report.id`, which broke as soon as two
  // downloads overlapped (starting B while A was still in flight
  // reassigned `.variables` to B, silently clearing A's spinner and
  // misattributing A's eventual error to B's row). Per-row state by
  // construction removes the shared-identity race instead of patching the
  // comparison.
  const downloadMutation = useMutation({
    mutationFn: () => downloadReport(report.id),
  });

  return (
    <div style={{ padding: "9px 0", borderBottom: "1px solid var(--line)" }}>
      <div className="row" style={{ gap: 13 }}>
        <span
          className="mono"
          style={{
            width: 76,
            flexShrink: 0,
            fontSize: 11,
            fontWeight: 500,
            textTransform: "uppercase",
            color: "var(--ink-2)",
          }}
        >
          {report.format}
        </span>
        <span style={{ flexGrow: 1, fontSize: 11, color: "var(--ink-3)" }}>
          {formatDateTime(report.generated_at)}
        </span>
        <button
          type="button"
          className="btn"
          style={{ width: 128 }}
          onClick={() => downloadMutation.mutate()}
          disabled={downloadMutation.isPending}
        >
          {downloadMutation.isPending ? <SpinnerIcon size={11} /> : <DownloadIcon />}
          {downloadMutation.isPending ? "Descargando" : "Descargar"}
        </button>
      </div>
      {downloadMutation.error && (
        <div style={{ marginTop: 8 }}>
          <ErrorBanner error={downloadMutation.error} />
        </div>
      )}
    </div>
  );
}

function ScanBanner({
  running,
  stalled,
  status,
  errorMessage,
  completedTools,
  toolCount,
  failedTools,
}: {
  running: boolean;
  stalled: boolean;
  status: ScanStatus;
  errorMessage: string | null;
  completedTools: number;
  toolCount: number;
  failedTools: string[];
}) {
  if (stalled) {
    return (
      <div className="callout callout--warn" style={{ marginBottom: 26 }}>
        <span style={{ color: "var(--warn)", flexShrink: 0, marginTop: 1 }}>
          <AlertIcon />
        </span>
        <div>
          <div className="callout__title">En curso desde hace más de 10 minutos</div>
          <div style={{ marginTop: 2 }}>
            Un pipeline normal tarda entre 4 y 6 minutos. Es probable que n8n haya abortado y el
            escaneo haya quedado en <span className="mono">running</span> sin nadie que lo cierre.
            Los hallazgos ya ingeridos siguen siendo válidos.
          </div>
        </div>
      </div>
    );
  }

  if (running) {
    return (
      <div className="callout callout--accent" style={{ marginBottom: 26 }}>
        <span style={{ color: "var(--accent-2)", flexShrink: 0, marginTop: 1 }}>
          <SpinnerIcon size={16} />
        </span>
        <div style={{ flexGrow: 1 }}>
          <div className="callout__title" style={{ color: "var(--accent-2)" }}>
            El pipeline sigue ejecutándose
          </div>
          <div style={{ marginTop: 2 }}>
            Tarda entre 4 y 6 minutos, dominado por el escaneo activo de ZAP. Los hallazgos
            aparecen a medida que cada herramienta termina.
          </div>
        </div>
        <span className="th" style={{ flexShrink: 0 }}>
          {completedTools} de {toolCount} herramientas completadas
        </span>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="callout callout--bad stack" style={{ marginBottom: 26, gap: 8 }}>
        <div className="row" style={{ gap: 9, color: "var(--bad)" }}>
          <AlertIcon />
          <span className="callout__title" style={{ color: "var(--bad)" }}>
            Escaneo fallido
          </span>
        </div>
        {errorMessage && <pre className="pre">{errorMessage}</pre>}
      </div>
    );
  }

  if (status === "cancelled") {
    return (
      <div className="callout callout--bad stack" style={{ marginBottom: 26, gap: 8 }}>
        <div className="row" style={{ gap: 9, color: "var(--bad)" }}>
          <AlertIcon />
          <span className="callout__title" style={{ color: "var(--bad)" }}>
            Escaneo cancelado
          </span>
        </div>
        <div>
          Corrieron {completedTools} de {toolCount} herramientas antes de la cancelación. Esta
          lista está incompleta.
        </div>
        {errorMessage && <pre className="pre">{errorMessage}</pre>}
      </div>
    );
  }

  // A scan can reach `completed` with individual tools failed. Saying the
  // list is complete in that case is exactly the "partial result reading
  // as a final one" failure this UI exists to avoid.
  if (failedTools.length > 0) {
    const names = failedTools.join(" y ");
    const verb = failedTools.length === 1 ? "falló" : "fallaron";
    return (
      <div className="callout callout--warn" style={{ marginBottom: 26 }}>
        <span style={{ color: "var(--warn)", flexShrink: 0, marginTop: 1 }}>
          <AlertIcon />
        </span>
        <div>
          <div className="callout__title">
            El pipeline terminó, pero {names} {verb}
          </div>
          <div style={{ marginTop: 2 }}>
            Corrieron {completedTools} de {toolCount} herramientas. Esta lista está incompleta: lo
            que {names} habría aportado no está acá, y el detalle del error figura más arriba.
          </div>
        </div>
      </div>
    );
  }

  // A tool whose *ingest call itself* failed (n8n's Ingest: * node, not the
  // scan itself) never gets a ScanTask row at all — invisible to the
  // `failedTools` check above, which only sees tasks that made it into the
  // database. n8n threads that gap into `error_message` even on an
  // otherwise-"completed" scan (see n8n/workflows/vulnscan-pipeline.json's
  // "Summarize Tool Failures" node) specifically so it doesn't read as a
  // clean, complete result here.
  if (errorMessage) {
    return (
      <div className="callout callout--warn stack" style={{ marginBottom: 26, gap: 8 }}>
        <div className="row" style={{ gap: 9 }}>
          <span style={{ color: "var(--warn)", flexShrink: 0, marginTop: 1 }}>
            <AlertIcon />
          </span>
          <div>
            <div className="callout__title">El pipeline terminó con advertencias</div>
            <div style={{ marginTop: 2 }}>
              Corrieron {completedTools} de {toolCount} herramientas registradas. Esta lista
              podría estar incompleta.
            </div>
          </div>
        </div>
        <pre className="pre">{errorMessage}</pre>
      </div>
    );
  }

  return (
    <div className="callout" style={{ marginBottom: 26 }}>
      <span style={{ color: "var(--ok)", flexShrink: 0, marginTop: 1 }}>
        <CheckIcon size={16} />
      </span>
      <div>
        <div className="callout__title">Terminaron las {toolCount} herramientas</div>
        <div style={{ marginTop: 2 }}>
          Todos los resultados fueron ingeridos y normalizados. Esta lista está completa.
        </div>
      </div>
    </div>
  );
}

function SortableHeader({
  label,
  sortKey,
  activeKey,
  direction,
  onSort,
  style,
}: {
  label: string;
  sortKey: SortKey;
  activeKey: SortKey;
  direction: SortDirection;
  onSort: (key: SortKey) => void;
  style?: CSSProperties;
}) {
  const active = sortKey === activeKey;
  return (
    <span
      role="columnheader"
      aria-sort={active ? (direction === "asc" ? "ascending" : "descending") : "none"}
      style={{ textAlign: "left", ...style }}
    >
      <button
        type="button"
        className="th th--sortable"
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: 0,
          fontFamily: "inherit",
          textAlign: "inherit",
          width: "100%",
        }}
        onClick={() => onSort(sortKey)}
      >
        {label}
        {active && <span aria-hidden="true">{direction === "asc" ? " ▲" : " ▼"}</span>}
      </button>
    </span>
  );
}

function FindingsTable({
  findings,
  total,
  toolCount,
  running,
  failedToLoad,
  openId,
  onToggle,
  toolFor,
  sortKey,
  sortDirection,
  onSort,
}: {
  findings: FindingRead[];
  total: number;
  toolCount: number;
  running: boolean;
  failedToLoad: boolean;
  openId: string | null;
  onToggle: (id: string) => void;
  toolFor: (finding: FindingRead) => string | null;
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
}) {
  return (
    <div className="tbl" role="table" aria-label="Hallazgos">
      <div className="tbl__head" role="row">
        <SortableHeader
          label="Severidad"
          sortKey="severity"
          activeKey={sortKey}
          direction={sortDirection}
          onSort={onSort}
          style={{ width: 100, flexShrink: 0 }}
        />
        <SortableHeader
          label="Título"
          sortKey="title"
          activeKey={sortKey}
          direction={sortDirection}
          onSort={onSort}
          style={{ flexGrow: 1, textAlign: "left" }}
        />
        <SortableHeader
          label="Tipo"
          sortKey="type"
          activeKey={sortKey}
          direction={sortDirection}
          onSort={onSort}
          style={{ width: 128, flexShrink: 0 }}
        />
        <SortableHeader
          label="Origen"
          sortKey="origin"
          activeKey={sortKey}
          direction={sortDirection}
          onSort={onSort}
          style={{ width: 74, flexShrink: 0 }}
        />
        <SortableHeader
          label="CVSS"
          sortKey="cvss"
          activeKey={sortKey}
          direction={sortDirection}
          onSort={onSort}
          style={{ width: 44, flexShrink: 0, textAlign: "right" }}
        />
      </div>

      {findings.map((finding) => {
        const open = openId === finding.id;
        const tool = toolFor(finding);
        return (
          <Fragment key={finding.id}>
            <button
              type="button"
              role="row"
              className={open ? "tbl__row tbl__row--clickable tbl__row--open" : "tbl__row tbl__row--clickable"}
              onClick={() => onToggle(finding.id)}
              aria-expanded={open}
            >
              <span role="cell" className="row" style={{ width: 100, flexShrink: 0, gap: 7 }}>
                <SeverityMeter severity={finding.severity} />
                <span className="sev-label" style={{ color: severityColor(finding.severity) }}>
                  {SEVERITY_META[finding.severity].label}
                </span>
              </span>
              <span role="cell" style={{ flexGrow: 1, fontSize: 13 }}>{finding.title}</span>
              <span
                role="cell"
                className="mono"
                style={{ width: 128, flexShrink: 0, fontSize: 11, color: "var(--ink-3)" }}
              >
                {finding.finding_type}
              </span>
              <span
                role="cell"
                className="mono"
                style={{ width: 74, flexShrink: 0, fontSize: 11, color: "var(--ink-2)" }}
              >
                {tool ? toolLabel(tool) : "—"}
              </span>
              <span
                role="cell"
                className="mono"
                style={{
                  width: 44,
                  flexShrink: 0,
                  fontSize: 12,
                  textAlign: "right",
                  color: "var(--ink-2)",
                }}
              >
                {finding.cvss_score ?? "—"}
              </span>
            </button>

            {open && <FindingDetail finding={finding} />}
          </Fragment>
        );
      })}

      {findings.length === 0 && (
        <EmptyState
          title={
            failedToLoad
              ? "No se pudieron cargar los hallazgos"
              : total === 0
                ? running
                  ? "Todavía no hay hallazgos"
                  : "El escaneo terminó sin hallazgos"
                : "Ningún hallazgo coincide con los filtros"
          }
        >
          {failedToLoad ? (
            <>
              Hubo un error de red o del servidor al pedir los hallazgos — no significa que el
              escaneo no haya producido ninguno. Reintentá recargando la página.
            </>
          ) : total === 0 ? (
            running ? (
              <>
                Nmap y WhatWeb aportan servicios y tecnologías, no hallazgos. Los primeros
                hallazgos aparecen cuando termina Nikto.
              </>
            ) : (
              <>
                Las {toolCount} herramientas corrieron y ninguna reportó nada. Esto es un
                resultado, no un error.
              </>
            )
          ) : (
            <>
              El escaneo sí produjo {total} hallazgos. Ampliá la selección de severidad o de
              herramienta.
            </>
          )}
        </EmptyState>
      )}
    </div>
  );
}

function FindingDetail({ finding }: { finding: FindingRead }) {
  return (
    <div
      style={{
        padding: "16px 16px 18px 129px",
        borderBottom: "1px solid var(--line)",
        background: "var(--panel-2)",
      }}
    >
      {finding.description && (
        <p
          style={{
            margin: "0 0 14px",
            fontSize: 12,
            lineHeight: 1.6,
            color: "var(--ink-2)",
            maxWidth: 760,
          }}
        >
          {finding.description}
        </p>
      )}

      {finding.evidence && (
        <>
          <div className="th" style={{ marginBottom: 6 }}>
            Evidencia
          </div>
          <pre className="pre" style={{ maxWidth: 860, marginBottom: 14 }}>
            {finding.evidence}
          </pre>
        </>
      )}

      <div className="row" style={{ gap: 32, flexWrap: "wrap", alignItems: "flex-start" }}>
        {finding.cvss_vector && (
          <div>
            <div className="th" style={{ marginBottom: 6 }}>
              Vector CVSS
            </div>
            <div
              className="mono"
              style={{
                fontSize: 11,
                color: "var(--ink-2)",
                overflowWrap: "anywhere",
                maxWidth: 330,
              }}
            >
              {finding.cvss_vector}
            </div>
          </div>
        )}

        <div>
          <div className="th" style={{ marginBottom: 6 }}>
            Referencias CVE
          </div>
          {finding.cve_references.length === 0 ? (
            <span style={{ fontSize: 11, color: "var(--ink-3)" }}>Sin CVE asociado</span>
          ) : (
            finding.cve_references.map((cve) => (
              <div key={cve.id} className="row" style={{ gap: 9, marginBottom: 4 }}>
                {/* Only http(s) is ever a real CVE reference URL - guards
                    against a javascript: URL from a compromised/malformed
                    upstream CVE feed executing on click. */}
                {cve.source_url && /^https?:\/\//i.test(cve.source_url) ? (
                  <a
                    href={cve.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mono"
                    style={{ fontSize: 12, fontWeight: 500 }}
                  >
                    {cve.cve_id}
                  </a>
                ) : (
                  <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>
                    {cve.cve_id}
                  </span>
                )}
                {cve.cvss_score !== null && (
                  <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>
                    CVSS {cve.cvss_score}
                  </span>
                )}
              </div>
            ))
          )}
        </div>

        {finding.confidence && (
          <div>
            <div className="th" style={{ marginBottom: 6 }}>
              Confianza
            </div>
            <span style={{ fontSize: 12, color: "var(--ink-2)" }}>{finding.confidence}</span>
          </div>
        )}
      </div>
    </div>
  );
}
