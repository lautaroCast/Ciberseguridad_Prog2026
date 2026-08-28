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

describe("ConfirmDialog while a confirm action is pending", () => {
  // 5th independent evaluation: only the confirm button respected `pending`
  // - Cancelar/Escape/backdrop-click all still called onCancel, so a user
  // who "cancelled" while the mutation was in flight had the dialog close
  // as if nothing was happening, while onConfirm's mutation (and its
  // onSuccess, e.g. a navigation) still ran moments later regardless.
  it("ignores Cancelar while pending", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        title="¿Confirmar?"
        confirmLabel="Eliminar todo"
        pending={true}
        onCancel={onCancel}
        onConfirm={vi.fn()}
      >
        contenido
      </ConfirmDialog>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("ignores Escape while pending", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        title="¿Confirmar?"
        confirmLabel="Eliminar todo"
        pending={true}
        onCancel={onCancel}
        onConfirm={vi.fn()}
      >
        contenido
      </ConfirmDialog>,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("ignores a backdrop click while pending", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        title="¿Confirmar?"
        confirmLabel="Eliminar todo"
        pending={true}
        onCancel={onCancel}
        onConfirm={vi.fn()}
      >
        contenido
      </ConfirmDialog>,
    );
    // Portaled to document.body (see ConfirmDialog.tsx), so the backdrop
    // is no longer inside render()'s own container - query the document.
    fireEvent.click(document.querySelector(".backdrop")!);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("still responds to Cancelar/Escape once pending clears", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        title="¿Confirmar?"
        confirmLabel="Eliminar todo"
        pending={false}
        onCancel={onCancel}
        onConfirm={vi.fn()}
      >
        contenido
      </ConfirmDialog>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});

describe("ConfirmDialog accessibility", () => {
  // 6th independent evaluation: the consequence text (the entire reason
  // this confirmation exists) had no id and was never wired via
  // aria-describedby, so a screen-reader user tabbing to Cancelar on open
  // heard only the title, not the irreversibility warning.
  it("associates its body content via aria-describedby", () => {
    render(
      <ConfirmDialog
        title="¿Confirmar?"
        confirmLabel="Eliminar todo"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      >
        contenido de advertencia
      </ConfirmDialog>,
    );
    const dialog = screen.getByRole("alertdialog");
    const describedById = dialog.getAttribute("aria-describedby");
    expect(describedById).toBeTruthy();
    expect(document.getElementById(describedById!)).toHaveTextContent(
      "contenido de advertencia",
    );
  });

  // 6th independent evaluation: the rest of the app (behind the backdrop)
  // was never marked inert/aria-hidden, so a screen reader's browse mode
  // could still read/interact with it while this modal was supposedly the
  // only thing open.
  it("marks #root inert while mounted and restores it on unmount", () => {
    const root = document.createElement("div");
    root.id = "root";
    document.body.appendChild(root);

    try {
      const { unmount } = render(
        <ConfirmDialog
          title="¿Confirmar?"
          confirmLabel="Eliminar todo"
          onCancel={vi.fn()}
          onConfirm={vi.fn()}
        >
          contenido
        </ConfirmDialog>,
      );
      expect(root.hasAttribute("inert")).toBe(true);

      unmount();
      expect(root.hasAttribute("inert")).toBe(false);
    } finally {
      root.remove();
    }
  });

  // 9th independent evaluation: closing the dialog (Cancelar/Escape/
  // backdrop/confirm) abandoned focus entirely instead of returning it to
  // whatever opened the dialog - a real gap for keyboard/screen-reader
  // users, who lost their place in the page after every interaction.
  it("restores focus to the triggering element on unmount", () => {
    const trigger = document.createElement("button");
    trigger.textContent = "Eliminar";
    document.body.appendChild(trigger);

    try {
      trigger.focus();
      expect(document.activeElement).toBe(trigger);

      const { unmount } = render(
        <ConfirmDialog
          title="¿Confirmar?"
          confirmLabel="Eliminar todo"
          onCancel={vi.fn()}
          onConfirm={vi.fn()}
        >
          contenido
        </ConfirmDialog>,
      );
      // The dialog moves focus to Cancelar on open, away from the trigger.
      expect(document.activeElement).not.toBe(trigger);

      unmount();
      expect(document.activeElement).toBe(trigger);
    } finally {
      trigger.remove();
    }
  });
});
