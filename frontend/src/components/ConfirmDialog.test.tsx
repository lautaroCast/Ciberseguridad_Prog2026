import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDialog } from "./ConfirmDialog";

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
});
