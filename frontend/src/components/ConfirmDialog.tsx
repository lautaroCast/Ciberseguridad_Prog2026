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

  useEffect(() => {
    cancelRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onCancel();
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
      <div className="dialog" role="alertdialog" aria-modal="true" aria-label={title}>
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
