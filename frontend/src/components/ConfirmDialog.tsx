import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

/**
 * Confirmation for irreversible actions.
 *
 * Deleting a target cascades in the database to its scans, findings and
 * reports, so the dialog states what else goes with it — the operator
 * cannot recover any of it from the dashboard afterwards.
 */
export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  onConfirm,
  onCancel,
  pending = false,
}: {
  title: string;
  children: ReactNode;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  pending?: boolean;
}) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCancel();
        return;
      }
      // Focus trap: without this, Tab/Shift+Tab can move focus out of the
      // dialog into the page behind the backdrop while it's still open and
      // modal (aria-modal="true") — a real gap for a destructive, cascading
      // confirmation like this one.
      if (event.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onCancel]);

  return (
    <div
      className="backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onCancel();
      }}
    >
      <div ref={dialogRef} className="dialog" role="alertdialog" aria-modal="true" aria-label={title}>
        <div className="empty__title" style={{ marginBottom: 7 }}>
          {title}
        </div>
        <div style={{ fontSize: 12, lineHeight: 1.6, color: "var(--ink-2)", marginBottom: 16 }}>
          {children}
        </div>
        <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
          <button ref={cancelRef} type="button" className="btn" onClick={onCancel}>
            Cancelar
          </button>
          <button
            type="button"
            className="btn btn--danger"
            onClick={onConfirm}
            disabled={pending}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
