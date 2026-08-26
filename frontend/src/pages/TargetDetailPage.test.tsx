import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { TargetRead } from "../types";

vi.mock("../api", () => ({
  getTarget: vi.fn(),
  listScansForTarget: vi.fn(),
  deleteTarget: vi.fn(),
  triggerPipeline: vi.fn(),
  updateTarget: vi.fn(),
  isTerminalStatus: (status: string) =>
    status === "completed" || status === "failed" || status === "cancelled",
}));

import { deleteTarget, getTarget, listScansForTarget, updateTarget } from "../api";
import { TargetDetailPage } from "./TargetDetailPage";

const ACTIVE_TARGET: TargetRead = {
  id: "target-1",
  name: "juice-shop-demo",
  host: "juice-shop",
  description: null,
  is_lab_target: true,
  is_active: true,
  created_at: "2026-08-21T00:00:00Z",
  updated_at: "2026-08-21T00:00:00Z",
};

function renderPage(queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/targets/target-1"]}>
        <Routes>
          <Route path="/targets/:id" element={<TargetDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("TargetDetailPage — reactivating a target", () => {
  beforeEach(() => {
    vi.mocked(getTarget).mockResolvedValue({ ...ACTIVE_TARGET, is_active: false });
    vi.mocked(listScansForTarget).mockResolvedValue([]);
    vi.mocked(updateTarget).mockResolvedValue({ ...ACTIVE_TARGET, is_active: true });
  });

  // Before this fix, `updateTarget` had zero callers anywhere in the
  // frontend — there was no UI path left to reactivate an inactive target.
  it("calls updateTarget with is_active: true when Reactivar is clicked", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Reactivar" }));
    await waitFor(() =>
      expect(updateTarget).toHaveBeenCalledWith("target-1", { is_active: true }),
    );
  });

  it("disables every 'Correr pipeline' button for an inactive target", async () => {
    renderPage();
    await screen.findByRole("button", { name: "Reactivar" });
    const runButtons = screen.getAllByRole("button", { name: "Correr pipeline" });
    expect(runButtons.length).toBeGreaterThan(0);
    for (const button of runButtons) expect(button).toBeDisabled();
  });
});

describe("TargetDetailPage — deleting a target", () => {
  it("disables the Eliminar button until the scan history has loaded", async () => {
    let resolveScans!: (scans: []) => void;
    vi.mocked(getTarget).mockResolvedValue(ACTIVE_TARGET);
    vi.mocked(listScansForTarget).mockReturnValue(
      new Promise((resolve) => {
        resolveScans = resolve;
      }),
    );

    renderPage();
    const deleteButton = await screen.findByRole("button", { name: "Eliminar" });
    expect(deleteButton).toBeDisabled();

    resolveScans([]);
    await screen.findByText("Este objetivo nunca se escaneó");
    expect(deleteButton).not.toBeDisabled();
  });

  // Before this fix, `disabled={!scansQuery.isSuccess}` meant a query that
  // *fails* never becomes true either — the button was stuck disabled
  // forever with no recovery path short of a full page reload.
  it("re-enables the Eliminar button when the scan history query errors, not just when it succeeds", async () => {
    vi.mocked(getTarget).mockResolvedValue(ACTIVE_TARGET);
    vi.mocked(listScansForTarget).mockRejectedValue(new Error("network error"));

    renderPage();
    const deleteButton = await screen.findByRole("button", { name: "Eliminar" });
    await waitFor(() => expect(deleteButton).not.toBeDisabled());
  });

  // 6th independent evaluation: the ErrorBanner for deleteMutation.error
  // used to render in the page's normal flow, underneath the open
  // ConfirmDialog's full-viewport backdrop - a failed delete left the
  // dialog sitting open with no visible explanation anywhere on screen.
  it("shows the delete error inside the still-open confirmation dialog", async () => {
    vi.mocked(getTarget).mockResolvedValue(ACTIVE_TARGET);
    vi.mocked(listScansForTarget).mockResolvedValue([]);
    vi.mocked(deleteTarget).mockRejectedValue(new Error("network error"));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Eliminar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Eliminar todo" }));

    expect(await screen.findByText("No se pudo contactar al backend")).toBeInTheDocument();
    // The dialog itself must still be open and showing the error, not
    // just some detached banner elsewhere on the page.
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
  });
});

describe("TargetDetailPage — a background refetch failing after data already loaded", () => {
  // 7th independent evaluation: `if (targetQuery.error) return <ErrorBanner/>`
  // used to be checked before `if (!targetQuery.data) return null` — since
  // TanStack Query never clears `data` on a failed background refetch, this
  // discarded a perfectly good, already-rendered target the instant any
  // later poll failed. The page must keep showing the target plus an inline
  // error banner, not go blank.
  it("keeps showing the already-loaded target instead of blanking out", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    vi.mocked(getTarget).mockResolvedValueOnce(ACTIVE_TARGET);
    vi.mocked(listScansForTarget).mockResolvedValue([]);

    renderPage(queryClient);
    await screen.findByRole("heading", { name: "juice-shop-demo" });

    vi.mocked(getTarget).mockRejectedValueOnce(new Error("network error"));
    await queryClient.refetchQueries({ queryKey: ["target", "target-1"] });

    expect(screen.getByRole("heading", { name: "juice-shop-demo" })).toBeInTheDocument();
    expect(await screen.findByText("No se pudo contactar al backend")).toBeInTheDocument();
  });
});
