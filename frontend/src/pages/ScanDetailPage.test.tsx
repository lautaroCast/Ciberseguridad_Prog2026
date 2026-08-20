import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FindingRead, ScanRead } from "../types";

// COD-12: description/evidence were fetched by the API but never rendered
// anywhere in the UI. This mocks the whole "../api" module (the same way
// ScanDetailPage imports it) so the component can be mounted without a
// real backend, and asserts the finding's detail row surfaces both fields
// once expanded. vitest hoists `vi.mock` above the imports below at
// transform time, so declaration order here doesn't matter.
vi.mock("../api", () => ({
  getScan: vi.fn(),
  listFindings: vi.fn(),
  listReports: vi.fn(),
  createReport: vi.fn(),
  downloadReport: vi.fn(),
  isTerminalStatus: (status: string) => status === "completed",
}));

import { getScan, listFindings, listReports } from "../api";
import { ScanDetailPage } from "./ScanDetailPage";

const SCAN: ScanRead = {
  id: "scan-1",
  target_id: "target-1",
  status: "completed",
  pipeline_run_id: null,
  triggered_by: null,
  started_at: null,
  finished_at: null,
  error_message: null,
  created_at: "2026-08-15T00:00:00Z",
};

const FINDING: FindingRead = {
  id: "finding-1",
  scan_id: "scan-1",
  scan_task_id: "task-1",
  service_id: null,
  title: "Cross-Domain Misconfiguration",
  description: "CORS misconfiguration allows arbitrary origins.",
  finding_type: "web_vulnerability",
  evidence: "Access-Control-Allow-Origin: *",
  confidence: null,
  cvss_score: 5.4,
  cvss_vector: null,
  severity: "medium",
  created_at: "2026-08-15T00:00:00Z",
  cve_references: [],
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/scans/scan-1"]}>
        <Routes>
          <Route path="/scans/:id" element={<ScanDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ScanDetailPage findings table", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listFindings).mockResolvedValue([FINDING]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  it("does not show description/evidence until the row is expanded", async () => {
    renderPage();
    await screen.findByText("Cross-Domain Misconfiguration");
    expect(screen.queryByText(/CORS misconfiguration/)).not.toBeInTheDocument();
  });

  it("shows description and evidence after clicking the row", async () => {
    renderPage();
    const titleCell = await screen.findByText("Cross-Domain Misconfiguration");
    fireEvent.click(titleCell);

    expect(await screen.findByText(/CORS misconfiguration allows arbitrary origins/)).toBeInTheDocument();
    expect(screen.getByText(/Access-Control-Allow-Origin: \*/)).toBeInTheDocument();
  });
});
