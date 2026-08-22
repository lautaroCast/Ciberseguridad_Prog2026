/** `4:19` — elapsed time in minutes and seconds. */
export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "—";
  const whole = Math.round(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/** Seconds between two ISO timestamps, or null when either is missing. */
export function elapsedSeconds(from: string | null, to: string | null): number | null {
  if (!from) return null;
  const start = new Date(from).getTime();
  const end = to ? new Date(to).getTime() : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end)) return null;
  return (end - start) / 1000;
}

/**
 * Strip ANSI color escapes from raw tool output.
 *
 * Tools write errors to a TTY-shaped stream: nuclei's failures arrive
 * wrapped in escape sequences, which render as literal `[1;31m` noise in
 * the middle of the message when shown as plain text.
 */
export function stripAnsi(text: string): string {
  // Two passes: the full escape (ESC + CSI + SGR), then any bare "[1;31m"
  // left behind when the ESC byte was dropped somewhere upstream.
  // Matching a control character is the whole point here.
  // oxlint-disable-next-line no-control-regex
  return text.replace(/\u001b\[[0-9;]*m/g, "").replace(/\[[0-9;]+m/g, "");
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
