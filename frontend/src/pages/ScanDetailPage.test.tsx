import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FindingRead, ScanRead, ScanTaskRead } from "../types";

vi.mock("../api", () => ({
  getScan: vi.fn(),
  listFindings: vi.fn(),
  listScanTasks: vi.fn(),
  listReports: vi.fn(),
  createReport: vi.fn(),
  downloadReport: vi.fn(),
  isTerminalStatus: (status: string) =>
    status === "completed" || status === "failed" || status === "cancelled",
}));

import { downloadReport, getScan, listFindings, listReports, listScanTasks } from "../api";
import { ScanDetailPage } from "./ScanDetailPage";
import type { ReportRead } from "../types";

const SCAN: ScanRead = {
  id: "scan-1",
  target_id: "target-1",
  status: "completed",
  pipeline_run_id: null,
  triggered_by: null,
  started_at: "2026-08-21T00:00:00Z",
  finished_at: "2026-08-21T00:04:19Z",
  error_message: null,
  created_at: "2026-08-21T00:00:00Z",
};

function task(id: string, toolName: string, status: ScanTaskRead["status"] = "completed"): ScanTaskRead {
  return {
    id,
    scan_id: "scan-1",
    tool_name: toolName,
    status,
    command: null,
    started_at: "2026-08-21T00:00:00Z",
    finished_at: "2026-08-21T00:01:00Z",
    error_message: status === "failed" ? "tool exited with code 1" : null,
    created_at: "2026-08-21T00:00:00Z",
  };
}

const CRITICAL: FindingRead = {
  id: "finding-1",
  scan_id: "scan-1",
  scan_task_id: "t-nuclei",
  service_id: null,
  title: "Apache Struts RCE",
  description: "OGNL injection through the Content-Type header.",
  finding_type: "template-match",
  evidence: "Content-Type: %{(#cmd=.id.)}",
  confidence: "firme",
  cvss_score: 10,
  cvss_vector: "CVSS:3.1/AV:N",
  severity: "critical",
  created_at: "2026-08-21T00:02:00Z",
  cve_references: [],
};

const INFO: FindingRead = {
  ...CRITICAL,
  id: "finding-2",
  scan_task_id: "t-zap",
  title: "Comentarios HTML sospechosos",
  description: null,
  evidence: null,
  cvss_score: null,
  cvss_vector: null,
  severity: "info",
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

describe("ScanDetailPage", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei"), task("t-zap", "zap")]);
    vi.mocked(listFindings).mockResolvedValue([CRITICAL, INFO]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  it("does not show description/evidence until the row is expanded", async () => {
    renderPage();
    await screen.findByText("Apache Struts RCE");
    expect(screen.queryByText(/OGNL injection/)).not.toBeInTheDocument();
  });

  it("shows description and evidence after clicking the row", async () => {
    renderPage();
    fireEvent.click(await screen.findByText("Apache Struts RCE"));
    expect(await screen.findByText(/OGNL injection/)).toBeInTheDocument();
    expect(screen.getByText(/#cmd=/)).toBeInTheDocument();
  });

  // Info findings dominate a real run (~21 of 32); showing them by default
  // buries the ones that need action.
  it("hides info findings by default and says how many are hidden", async () => {
    renderPage();
    await screen.findByText("Apache Struts RCE");
    expect(screen.queryByText("Comentarios HTML sospechosos")).not.toBeInTheDocument();
    expect(screen.getByText("1 de 2")).toBeInTheDocument();
  });

  it("reveals info findings when the severity chip is toggled on", async () => {
    renderPage();
    await screen.findByText("Apache Struts RCE");
    fireEvent.click(screen.getByRole("button", { name: /Informativa/ }));
    expect(await screen.findByText("Comentarios HTML sospechosos")).toBeInTheDocument();
  });

  // Tool attribution is only derivable by joining findings to scan_tasks.
  it("attributes each finding to its tool", async () => {
    renderPage();
    await screen.findByText("Apache Struts RCE");
    expect(screen.getAllByText("Nuclei").length).toBeGreaterThan(0);
  });

  it("filters findings out when their tool chip is toggled off", async () => {
    renderPage();
    await screen.findByText("Apache Struts RCE");
    fireEvent.click(screen.getByRole("button", { name: /^nuclei/ }));
    expect(screen.queryByText("Apache Struts RCE")).not.toBeInTheDocument();
  });

  // The severity distribution is partly an artifact of the platform's own
  // classification policy; the UI must say so rather than present it raw.
  it("states the severity-scale bias next to the per-tool breakdown", async () => {
    renderPage();
    expect(
      await screen.findByText(/condicionada por la política de clasificación/),
    ).toBeInTheDocument();
  });

  it("surfaces a failed tool without hiding the ones that succeeded", async () => {
    vi.mocked(listScanTasks).mockResolvedValue([
      task("t-nuclei", "nuclei"),
      task("t-nikto", "nikto", "failed"),
    ]);
    renderPage();
    expect(
      await screen.findByText(/el pipeline continuó con las herramientas restantes/),
    ).toBeInTheDocument();
    expect(screen.getByText(/tool exited with code 1/)).toBeInTheDocument();
  });
});

describe("ScanDetailPage while the pipeline runs", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue({ ...SCAN, status: "running", finished_at: null });
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei")]);
    vi.mocked(listFindings).mockResolvedValue([CRITICAL]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  // A partial result must never read as a final one.
  it("marks the findings list as incomplete", async () => {
    renderPage();
    expect(await screen.findByText(/lista incompleta/)).toBeInTheDocument();
    expect(screen.getByText("Escaneo en curso")).toBeInTheDocument();
  });

  it("does not offer report generation before the scan finishes", async () => {
    renderPage();
    await screen.findByText(/lista incompleta/);
    expect(screen.queryByRole("button", { name: /Generar PDF/ })).not.toBeInTheDocument();
  });
});

describe("ScanDetailPage when a tool failed but the scan completed", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listScanTasks).mockResolvedValue([
      task("t-zap", "zap"),
      task("t-nuclei", "nuclei", "failed"),
    ]);
    vi.mocked(listFindings).mockResolvedValue([]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  // A scan reaches `completed` even when individual tools failed. Claiming
  // the list is complete there is the exact failure this UI exists to avoid.
  it("does not claim the list is complete", async () => {
    renderPage();
    expect(await screen.findByText(/pero Nuclei falló/)).toBeInTheDocument();
    expect(screen.queryByText(/Esta lista está completa/)).not.toBeInTheDocument();
    expect(screen.getByText(/Esta lista está incompleta/)).toBeInTheDocument();
  });
});

describe("ScanDetailPage when the scan was cancelled", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue({
      ...SCAN,
      status: "cancelled",
      error_message: "cancelado por el operador",
    });
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei"), task("t-zap", "zap")]);
    vi.mocked(listFindings).mockResolvedValue([]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  // Before this fix, a cancelled scan with no individually-failed tool fell
  // through to the default "success" banner.
  it("shows a cancelled banner instead of claiming success", async () => {
    renderPage();
    expect(await screen.findByText("Escaneo cancelado")).toBeInTheDocument();
    expect(screen.getByText(/cancelado por el operador/)).toBeInTheDocument();
    expect(screen.queryByText(/Esta lista está completa/)).not.toBeInTheDocument();
  });
});

describe("ScanDetailPage with more than five tools reported", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue({ ...SCAN, status: "running", finished_at: null });
    vi.mocked(listScanTasks).mockResolvedValue([
      task("t-nmap", "nmap"),
      task("t-whatweb", "whatweb"),
      task("t-nikto", "nikto"),
      task("t-nuclei", "nuclei"),
      task("t-zap", "zap"),
      task("t-sqlmap", "sqlmap"),
    ]);
    vi.mocked(listFindings).mockResolvedValue([]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  // buildToolBreakdown appends any backend-reported tool outside TOOL_ORDER
  // (lib/tools.ts) as an extra row — before this fix, the "faltan X de 5"
  // count went negative once a 6th tool's task showed up completed.
  it("derives the tool count instead of hardcoding 5", async () => {
    renderPage();
    expect(await screen.findByText(/faltan 0 de 6 herramientas/)).toBeInTheDocument();
  });
});

describe("ScanDetailPage findings table sorting", () => {
  const ALPHA: FindingRead = { ...CRITICAL, id: "f-a", title: "Alpha", severity: "high", cvss_score: 5 };
  const BETA: FindingRead = { ...CRITICAL, id: "f-b", title: "Beta", severity: "high", cvss_score: 9 };
  const GAMMA: FindingRead = { ...CRITICAL, id: "f-c", title: "Gamma", severity: "high", cvss_score: 2 };

  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei")]);
    vi.mocked(listFindings).mockResolvedValue([ALPHA, BETA, GAMMA]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  it("sorts by CVSS ascending when the CVSS header is clicked", async () => {
    renderPage();
    await screen.findByText("Alpha");
    fireEvent.click(screen.getByRole("button", { name: /CVSS/ }));
    const order = screen
      .getAllByText(/^(Alpha|Beta|Gamma)$/)
      .map((el) => el.textContent);
    expect(order).toEqual(["Gamma", "Alpha", "Beta"]);
  });

  it("reverses direction on a second click of the same header", async () => {
    renderPage();
    await screen.findByText("Alpha");
    const cvssHeader = screen.getByRole("button", { name: /CVSS/ });
    fireEvent.click(cvssHeader);
    fireEvent.click(cvssHeader);
    const order = screen
      .getAllByText(/^(Alpha|Beta|Gamma)$/)
      .map((el) => el.textContent);
    expect(order).toEqual(["Beta", "Alpha", "Gamma"]);
  });
});

describe("ScanDetailPage when the findings request itself fails", () => {
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei"), task("t-zap", "zap")]);
    vi.mocked(listFindings).mockRejectedValue(new Error("network down"));
    vi.mocked(listReports).mockResolvedValue([]);
  });

  // Before this fix, a failed findingsQuery left `findings=[]`/`total=0`,
  // which for a non-running scan rendered the confident (and false) claim
  // "esto es un resultado, no un error" right next to the real ErrorBanner
  // that contradicted it.
  it("does not claim the empty list is a real result", async () => {
    renderPage();
    await screen.findByText("No se pudieron cargar los hallazgos");
    expect(
      screen.queryByText(/ninguna reportó nada\. Esto es un resultado, no un error/),
    ).not.toBeInTheDocument();
  });
});

describe("ScanDetailPage report downloads", () => {
  const REPORT_A: ReportRead = {
    id: "report-a",
    scan_id: "scan-1",
    format: "pdf",
    file_path: "scan-1.pdf",
    generated_at: "2026-08-21T00:05:00Z",
    generated_by: null,
  };
  const REPORT_B: ReportRead = {
    id: "report-b",
    scan_id: "scan-1",
    format: "html",
    file_path: "scan-1.html",
    generated_at: "2026-08-21T00:05:00Z",
    generated_by: null,
  };

  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei")]);
    vi.mocked(listFindings).mockResolvedValue([]);
    vi.mocked(listReports).mockResolvedValue([REPORT_A, REPORT_B]);
  });

  // Before this fix, a single useMutation shared across every report row
  // identified "which row is this" by comparing `.variables` to the row's
  // report id — starting B's download while A's was still in flight
  // reassigned `.variables` to B, so A's spinner disappeared and A's
  // eventual error would have been attributed to B's row instead.
  it("keeps concurrent downloads independent per row", async () => {
    let resolveA: () => void = () => {};
    const pendingA = new Promise<void>((resolve) => {
      resolveA = resolve;
    });
    vi.mocked(downloadReport).mockImplementation((reportId: string) =>
      reportId === "report-a" ? pendingA : Promise.reject(new Error("descarga falló")),
    );

    renderPage();
    const downloadButtons = await screen.findAllByRole("button", { name: /Descargar/ });
    expect(downloadButtons).toHaveLength(2);

    fireEvent.click(downloadButtons[0]); // start downloading A (stays pending)
    await screen.findAllByText("Descargando");

    fireEvent.click(downloadButtons[1]); // B fails while A is still in flight
    await screen.findByText("No se pudo contactar al backend");

    // A's row must still read as downloading — B's outcome must not have
    // touched it.
    expect(screen.getAllByText("Descargando")).toHaveLength(1);

    resolveA();
  });
});
