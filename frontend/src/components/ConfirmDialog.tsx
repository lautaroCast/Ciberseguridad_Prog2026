import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
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
  const descriptionId = useId();

  // onCancel is an inline arrow function at the one real call site
  // (TargetDetailPage.tsx), a fresh identity on every render — and that
  // component re-renders every 4s while any scan is non-terminal (its own
  // refetchInterval). A ref sidesteps that entirely: the effect below runs
  // once (mount only), so the initial focus() call fires exactly once
  // instead of stealing focus back on every unrelated parent re-render,
  // while onKeyDown still always calls the latest onCancel via the ref
  // (no stale-closure risk from never re-running the effect).
  const onCancelRef = useRef(onCancel);
  const pendingRef = useRef(pending);
  useEffect(() => {
    onCancelRef.current = onCancel;
    pendingRef.current = pending;
  });

  useEffect(() => {
    cancelRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        // pending: the confirm action is already in flight and can't be
        // un-done from here — closing the dialog now would just make the
        // user think they backed out while onConfirm's mutation still
        // resolves (and its onSuccess still runs) moments later.
        if (!pendingRef.current) onCancelRef.current();
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
  }, []); // mount-only, deliberately — see onCancelRef above for why

  // The dialog is portaled to document.body (below) specifically so this
  // can mark the real app content `inert` without also making the dialog
  // itself inert — both would otherwise live under #root, and `inert`
  // applies to the whole subtree it's set on. The Tab-key focus trap above
  // only constrains linear keyboard navigation; `inert` additionally
  // removes background content from the accessibility tree entirely, so a
  // screen reader's browse/virtual-cursor mode can't read or interact with
  // it while this destructive confirmation is open.
  useEffect(() => {
    const root = document.getElementById("root");
    root?.setAttribute("inert", "");
    return () => root?.removeAttribute("inert");
  }, []);

  return createPortal(
    <div
      className="backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget && !pending) onCancel();
      }}
    >
      <div
        ref={dialogRef}
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-label={title}
        aria-describedby={descriptionId}
      >
        <div className="empty__title" style={{ marginBottom: 7 }}>
          {title}
        </div>
        <div
          id={descriptionId}
          style={{ fontSize: 12, lineHeight: 1.6, color: "var(--ink-2)", marginBottom: 16 }}
        >
          {children}
        </div>
        <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
          <button
            ref={cancelRef}
            type="button"
            className="btn"
            onClick={() => {
              if (!pending) onCancel();
            }}
          >
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
    </div>,
    document.body,
  );
}
