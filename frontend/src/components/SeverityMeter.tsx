import { SEVERITY_META, severityColor } from "../lib/severity";
import type { Severity } from "../types";

/**
 * Five-step rank meter — the non-color half of the severity encoding.
 *
 * Filled steps carry the ordinal rank (critical 5 … info 1), so severity
 * stays readable in grayscale and with any color vision deficiency. The
 * meter is decorative on its own; callers always render the severity name
 * next to it, and that text is what assistive technology reads.
 */
export function SeverityMeter({ severity }: { severity: Severity }) {
  const { rank } = SEVERITY_META[severity];
  return (
    <span className="meter" style={{ color: severityColor(severity) }} aria-hidden="true">
      {[1, 2, 3, 4, 5].map((step) => (
        <span key={step} className={step <= rank ? "meter__step meter__step--on" : "meter__step"} />
      ))}
    </span>
  );
}
