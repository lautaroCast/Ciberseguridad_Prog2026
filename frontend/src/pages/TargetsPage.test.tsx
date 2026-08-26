import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ScanRead, TargetRead } from "../types";

// TargetsPage imports isTerminalStatus from "../api/scans" directly, not
// from "../api" — a separate module identity to vitest, so mocking "../api"
// alone would leave this one unmocked.
vi.mock("../api", () => ({
  createTarget: vi.fn(),
  listScansForTarget: vi.fn(),
  listTargets: vi.fn(),
}));
vi.mock("../api/scans", () => ({
  isTerminalStatus: (status: string) =>
    status === "completed" || status === "failed" || status === "cancelled",
}));

import { createTarget, listScansForTarget, listTargets } from "../api";
import { TargetsPage } from "./TargetsPage";

const TARGET: TargetRead = {
  id: "target-1",
  name: "juice-shop-demo",
  host: "juice-shop",
  description: null,
  is_lab_target: true,
  is_active: true,
  created_at: "2026-08-21T00:00:00Z",
  updated_at: "2026-08-21T00:00:00Z",
};

function scan(overrides: Partial<ScanRead> = {}): ScanRead {
  return {
    id: "scan-1",
    target_id: "target-1",
    status: "completed",
    pipeline_run_id: null,
    triggered_by: null,
    started_at: "2026-08-21T00:00:00Z",
    finished_at: "2026-08-21T00:04:00Z",
    error_message: null,
    created_at: "2026-08-21T00:00:00Z",
    ...overrides,
  };
}

function renderPage(queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/targets"]}>
        <Routes>
          <Route path="/targets" element={<TargetsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("TargetsPage", () => {
  beforeEach(() => {
    vi.mocked(listTargets).mockResolvedValue([TARGET]);
    vi.mocked(listScansForTarget).mockResolvedValue([scan()]);
    vi.mocked(createTarget).mockResolvedValue(TARGET);
  });

  it("shows the empty state when there are no targets registered", async () => {
    vi.mocked(listTargets).mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText("Todavía no hay objetivos registrados")).toBeInTheDocument();
  });

  it("lists a registered target with a link to its last scan", async () => {
    renderPage();
    expect(await screen.findByText("juice-shop-demo")).toBeInTheDocument();
    // Terminal scans show their date, not the status label (that's only
    // shown while running) — the link itself is the reliable signal that
    // the last-scan row rendered at all.
    const links = screen.getAllByRole("link");
    expect(links.some((link) => link.getAttribute("href") === "/scans/scan-1")).toBe(true);
  });

  it("shows 'nunca escaneado' when a target has no scan history", async () => {
    vi.mocked(listScansForTarget).mockResolvedValue([]);
    renderPage();
    await screen.findByText("juice-shop-demo");
    expect(screen.getByText("nunca escaneado")).toBeInTheDocument();
  });

  // 8th independent evaluation: `scanHistoryFailed` used to be checked
  // before whether `scanQuery.data` still had a value from an earlier
  // successful fetch - a single transient poll error hid an already-known
  // last-scan link behind "no se pudo cargar".
  it("keeps showing the last-scan link instead of hiding it after a later poll fails", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    vi.mocked(listScansForTarget).mockResolvedValueOnce([scan()]);

    renderPage(queryClient);
    await screen.findByText("juice-shop-demo");
    const linksBefore = screen.getAllByRole("link");
    expect(linksBefore.some((link) => link.getAttribute("href") === "/scans/scan-1")).toBe(true);

    vi.mocked(listScansForTarget).mockRejectedValueOnce(new Error("network error"));
    await queryClient.refetchQueries({ queryKey: ["target-scans", "target-1"] });

    await waitFor(() => {
      const links = screen.getAllByRole("link");
      expect(links.some((link) => link.getAttribute("href") === "/scans/scan-1")).toBe(true);
    });
    expect(screen.queryByText("no se pudo cargar")).not.toBeInTheDocument();
  });

  it("disables the Registrar button until a name is entered", async () => {
    renderPage();
    const submit = await screen.findByRole("button", { name: /Registrar/ });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "DVWA local" } });
    expect(submit).not.toBeDisabled();
  });

  it("submits the registration form with the selected host", async () => {
    renderPage();
    await screen.findByText("juice-shop-demo");

    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "DVWA local" } });
    fireEvent.click(screen.getByRole("button", { name: "dvwa" }));
    fireEvent.click(screen.getByRole("button", { name: /Registrar/ }));

    await waitFor(() =>
      expect(createTarget).toHaveBeenCalledWith({
        name: "DVWA local",
        host: "dvwa",
        description: null,
      }),
    );
  });
});
