import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDialog } from "./ConfirmDialog";

/** Mirrors the one real call site (TargetDetailPage.tsx): onCancel is a
 * fresh inline arrow function every render, and a `tick` state lets the
 * test force unrelated re-renders the same way that page's own polling
 * (refetchInterval) does in production. */
function UnstableCallbackHarness() {
  const [tick, setTick] = useState(0);
  return (
    <div>
      <button type="button" onClick={() => setTick((n) => n + 1)}>
        force re-render
      </button>
      <span data-testid="tick">{tick}</span>
      <ConfirmDialog
        title="¿Confirmar?"
        confirmLabel="Eliminar todo"
        onCancel={() => {}}
        onConfirm={vi.fn()}
      >
        contenido
      </ConfirmDialog>
    </div>
  );
}

function renderDialog(pending = false) {
  return render(
    <ConfirmDialog
      title="¿Confirmar?"
      confirmLabel="Eliminar todo"
      pending={pending}
      onCancel={vi.fn()}
      onConfirm={vi.fn()}
    >
      contenido
    </ConfirmDialog>,
  );
}

describe("ConfirmDialog focus trap", () => {
  // Before this fix, Tab/Shift+Tab had no handling at all — focus could
  // leave the dialog into the page behind the backdrop while it was still
  // open and modal, a real gap for a destructive, cascading confirmation.
  it("wraps Tab from the last focusable element back to the first", async () => {
    renderDialog();
    const cancel = screen.getByRole("button", { name: "Cancelar" });
    const confirm = screen.getByRole("button", { name: "Eliminar todo" });

    confirm.focus();
    expect(document.activeElement).toBe(confirm);

    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(cancel);
  });

  it("wraps Shift+Tab from the first focusable element back to the last", async () => {
    renderDialog();
    const cancel = screen.getByRole("button", { name: "Cancelar" });
    const confirm = screen.getByRole("button", { name: "Eliminar todo" });

    cancel.focus();
    expect(document.activeElement).toBe(cancel);

    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(confirm);
  });

  it("excludes the disabled confirm button from the trap while pending", async () => {
    renderDialog(true);
    const cancel = screen.getByRole("button", { name: "Cancelar" });

    cancel.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    // Only one enabled focusable element (Cancelar) — Tab keeps it focused.
    expect(document.activeElement).toBe(cancel);
  });

  // Regression: the initial-focus effect used to depend on [onCancel]. The
  // one real caller (TargetDetailPage.tsx) passes a fresh inline onCancel
  // every render, and re-renders every 4s while a scan is non-terminal
  // (its own refetchInterval) — each of those re-renders re-ran the
  // effect and stole focus back to "Cancelar" mid-interaction, even
  // though nothing about the dialog itself changed.
  it("does not steal focus back to Cancelar when the parent re-renders with a new onCancel identity", () => {
    render(<UnstableCallbackHarness />);
    const confirm = screen.getByRole("button", { name: "Eliminar todo" });

    confirm.focus();
    expect(document.activeElement).toBe(confirm);

    fireEvent.click(screen.getByRole("button", { name: "force re-render" }));
    expect(screen.getByTestId("tick")).toHaveTextContent("1");
    expect(document.activeElement).toBe(confirm);
  });
});
