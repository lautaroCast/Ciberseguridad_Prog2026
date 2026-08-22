import { SeverityMeter } from "./SeverityMeter";
import { SEVERITY_META, severityColor } from "../lib/severity";
import type { Severity } from "../types";

/** Rank meter + name. The name is the accessible label, not the color. */
export function SeverityBadge({ severity }: { severity: Severity }) {
  const { label } = SEVERITY_META[severity];
  return (
    <span className="row" style={{ gap: 7 }}>
      <SeverityMeter severity={severity} />
      <span className="sev-label" style={{ color: severityColor(severity) }}>
        {label}
      </span>
    </span>
  );
}
