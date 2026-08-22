import { StatusIcon } from "./StatusIcon";
import { statusColor, statusLabel } from "../lib/status";
import { elapsedSeconds, formatDuration, stripAnsi } from "../lib/format";
import type { ToolBreakdownRow } from "../lib/tools";

function resultText(row: ToolBreakdownRow): string {
  const status = row.task?.status;
  if (status === "failed") return "error";
  if (status === "running") return "ejecutando…";
  if (!row.task) return "en cola";
  if (status === "pending") return "en cola";
  if (status === "skipped") return "omitida";
  if (!row.producesFindings) return "no aporta hallazgos";
  return row.total === 1 ? "1 hallazgo" : `${row.total} hallazgos`;
}

/**
 * Per-tool progress, straight from `GET /scans/{id}/tasks`.
 *
 * The scan's own `status` collapses five sequential tools into a single
 * value, so on its own it cannot distinguish "nmap just started" from
 * "ZAP is halfway through a four-minute active scan". This is the view
 * that makes the wait legible.
 */
export function ToolTimeline({ rows }: { rows: ToolBreakdownRow[] }) {
  const durations = rows.map((row) =>
    row.task ? (elapsedSeconds(row.task.started_at, row.task.finished_at) ?? 0) : 0,
  );
  const longest = Math.max(...durations, 1);

  return (
    <div className="tbl">
      {rows.map((row, index) => {
        const task = row.task;
        const status = task?.status ?? "pending";
        const seconds = durations[index];
        const running = status === "running";
        const width = running ? 46 : Math.round((seconds / longest) * 100);
        const barColor =
          status === "failed"
            ? "var(--bad)"
            : running
              ? "var(--accent)"
              : status === "completed"
                ? "var(--ok)"
                : "var(--line-2)";

        return (
          <div
            key={row.tool}
            className="tbl__row"
            style={{ background: running ? "var(--accent-bg)" : undefined }}
          >
            <span
              style={{ color: statusColor(status), display: "flex", width: 18, flexShrink: 0 }}
              title={statusLabel(status)}
            >
              <StatusIcon status={status} size={16} />
            </span>

            <span
              className="mono"
              style={{
                width: 92,
                flexShrink: 0,
                fontSize: 13,
                fontWeight: 500,
                color: task ? "var(--ink)" : "var(--ink-3)",
              }}
            >
              {row.label}
            </span>

            <span style={{ width: 212, flexShrink: 0, fontSize: 12, color: "var(--ink-3)" }}>
              {row.role}
            </span>

            <div className="row" style={{ flexGrow: 1, gap: 10 }}>
              <div
                style={{
                  flexGrow: 1,
                  height: 4,
                  borderRadius: 2,
                  background: "var(--panel-2)",
                  overflow: "hidden",
                }}
              >
                <div style={{ height: "100%", width: `${width}%`, background: barColor }} />
              </div>
              <span
                className="mono"
                style={{ fontSize: 11, color: "var(--ink-3)", width: 42, textAlign: "right" }}
              >
                {seconds > 0 || running ? formatDuration(seconds) : "—"}
              </span>
            </div>

            <span
              style={{
                width: 132,
                flexShrink: 0,
                textAlign: "right",
                fontSize: 12,
                color: status === "failed" ? "var(--bad)" : "var(--ink-2)",
              }}
            >
              {resultText(row)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** Error detail for tools that failed while the rest of the scan carried on. */
export function ToolErrors({ rows }: { rows: ToolBreakdownRow[] }) {
  const failed = rows.filter((row) => row.task?.status === "failed" && row.task.error_message);
  if (failed.length === 0) return null;

  return (
    <div className="stack" style={{ gap: 10, marginTop: 16 }}>
      {failed.map((row) => (
        <div key={row.tool} className="callout callout--bad stack" style={{ gap: 8 }}>
          <div className="row" style={{ gap: 8, color: "var(--bad)" }}>
            <AlertGlyph />
            <span style={{ fontSize: 13, fontWeight: 500 }}>
              {row.label} falló — el pipeline continuó con las herramientas restantes
            </span>
          </div>
          <pre className="pre">{stripAnsi(row.task?.error_message ?? "")}</pre>
        </div>
      ))}
    </div>
  );
}

function AlertGlyph() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.2}
      strokeLinecap="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" />
      <path d="M12 16.5v.01" />
    </svg>
  );
}
