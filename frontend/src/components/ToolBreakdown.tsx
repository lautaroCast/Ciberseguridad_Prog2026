import { InfoIcon } from "./Icon";
import { SEVERITY_META, SEVERITY_ORDER, severityColor } from "../lib/severity";
import type { ToolBreakdownRow } from "../lib/tools";

/**
 * Severity distribution broken down by the tool that produced it.
 *
 * Deliberately placed above the findings table rather than as a column
 * inside it. The platform's classification policy constrains what each
 * tool can report — ZAP's four-level scale can never reach `critical`,
 * and Nikto's findings are all forced to `low` — so an aggregate severity
 * chart reads as a property of the target when it is substantially an
 * artifact of those rules. The caveat below is part of the chart, not a
 * footnote.
 */
export function ToolBreakdown({ rows }: { rows: ToolBreakdownRow[] }) {
  const maxTotal = Math.max(...rows.map((row) => row.total), 1);
  const biased = rows.filter((row) => row.bias && row.total > 0);

  return (
    <>
      <div className="tbl" style={{ marginBottom: 12 }}>
        {rows.map((row) => (
          <div key={row.tool} className="tbl__row">
            <span
              className="mono"
              style={{
                width: 92,
                flexShrink: 0,
                fontSize: 12,
                fontWeight: 500,
                color: row.total > 0 ? "var(--ink)" : "var(--ink-3)",
              }}
            >
              {row.label}
            </span>

            <span
              className="mono"
              style={{
                width: 30,
                flexShrink: 0,
                fontSize: 12,
                textAlign: "right",
                color: "var(--ink-2)",
              }}
            >
              {row.total > 0 ? row.total : "—"}
            </span>

            <div
              className="row"
              style={{
                flexGrow: 1,
                height: 14,
                borderRadius: 3,
                overflow: "hidden",
                background: "var(--panel-2)",
                gap: 1,
              }}
            >
              {SEVERITY_ORDER.filter((severity) => row.counts[severity] > 0).map((severity) => (
                <div
                  key={severity}
                  title={`${SEVERITY_META[severity].label}: ${row.counts[severity]}`}
                  style={{
                    width: `${(row.counts[severity] / maxTotal) * 100}%`,
                    background: severityColor(severity),
                    opacity: 0.85,
                  }}
                />
              ))}
            </div>

            <span
              style={{
                width: 320,
                flexShrink: 0,
                fontSize: 11,
                color: "var(--ink-3)",
                textAlign: "right",
              }}
            >
              {row.total === 0 && !row.producesFindings
                ? `aporta ${row.tool === "nmap" ? "servicios" : "tecnologías"}, no hallazgos`
                : (row.bias ?? "")}
            </span>
          </div>
        ))}
      </div>

      {biased.length > 0 && (
        <div className="callout callout--warn" style={{ marginBottom: 26 }}>
          <span style={{ color: "var(--warn)", flexShrink: 0, marginTop: 1 }}>
            <InfoIcon />
          </span>
          <div>
            <strong style={{ color: "var(--ink)", fontWeight: 600 }}>
              La distribución de severidad está condicionada por la política de clasificación.
            </strong>{" "}
            La escala de ZAP llega hasta <em>alta</em>, así que ninguna de sus alertas puede
            clasificarse como crítica; Nikto se fuerza íntegramente a <em>baja</em>. La fila
            «crítica» solo puede alimentarse de Nuclei. Leer esta distribución como una propiedad
            del objetivo, y no en parte como un artefacto del criterio, sería incorrecto.
          </div>
        </div>
      )}
    </>
  );
}
