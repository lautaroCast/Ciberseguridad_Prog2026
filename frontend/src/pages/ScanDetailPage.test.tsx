import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

function renderPage(queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
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

  // 8th independent evaluation: cve.source_url used to render as <a href>
  // with no scheme check - a compromised/malformed upstream CVE feed
  // could inject a javascript: URL that executes on click.
  it("does not render a CVE reference with a non-http(s) source_url as a link", async () => {
    const UNSAFE_CVE = {
      ...CRITICAL,
      id: "finding-unsafe-cve",
      title: "Unsafe CVE Source",
      cve_references: [
        {
          id: "cve-1",
          cve_id: "CVE-2099-0001",
          cvss_score: null,
          cvss_vector: null,
          description: null,
          source_url: "javascript:alert(1)",
        },
      ],
    };
    vi.mocked(listFindings).mockResolvedValue([UNSAFE_CVE]);

    renderPage();
    fireEvent.click(await screen.findByText("Unsafe CVE Source"));

    const cveText = await screen.findByText("CVE-2099-0001");
    expect(cveText.tagName).toBe("SPAN");
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

describe("ScanDetailPage strips ANSI escapes from scan.error_message", () => {
  // 9th independent evaluation: ToolTimeline already stripped ANSI escapes
  // from a task's error_message, but ScanBanner rendered the scan-level
  // error_message raw in 3 places (failed/cancelled/completed-with-
  // warnings) - real nuclei output can carry literal SGR escapes.
  const ESC = String.fromCharCode(27);

  it("does not render raw ANSI escape codes in the failed-scan banner", async () => {
    vi.mocked(getScan).mockResolvedValue({
      ...SCAN,
      status: "failed",
      error_message: `[${ESC}[1;31mFTL${ESC}[0m] Could not run nuclei: no templates provided for scan`,
    });
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei")]);
    vi.mocked(listFindings).mockResolvedValue([]);
    vi.mocked(listReports).mockResolvedValue([]);

    renderPage();
    expect(await screen.findByText("Escaneo fallido")).toBeInTheDocument();
    expect(
      screen.getByText("[FTL] Could not run nuclei: no templates provided for scan"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/\[1;31m/)).not.toBeInTheDocument();
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

describe("ScanDetailPage when a tool's ingest call itself failed (no ScanTask row, only Scan.error_message)", () => {
  beforeEach(() => {
    // No "failed" ScanTask row here on purpose - this is the case where
    // n8n's Ingest node call itself never landed, so the tool has no
    // ScanTask row at all, unlike the "tool ran, ScanTask.status=failed"
    // case covered by "surfaces a failed tool without hiding the ones
    // that succeeded" above.
    vi.mocked(getScan).mockResolvedValue({
      ...SCAN,
      error_message: "Tools that failed to ingest results: Nikto.",
    });
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei"), task("t-zap", "zap")]);
    vi.mocked(listFindings).mockResolvedValue([]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  it("shows a warning banner instead of claiming a clean, complete result", async () => {
    renderPage();
    expect(await screen.findByText("El pipeline terminó con advertencias")).toBeInTheDocument();
    expect(screen.getByText(/Tools that failed to ingest results: Nikto\./)).toBeInTheDocument();
    expect(screen.queryByText(/Todos los resultados fueron ingeridos/)).not.toBeInTheDocument();
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

describe("ScanDetailPage forces one more fetch when the scan finishes", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  // 5th independent evaluation: refetchInterval flipping to `false` on the
  // running->terminal transition only stops *future* polling of
  // tasksQuery/findingsQuery - it never guaranteed one last fetch, unlike
  // reportsQuery's `enabled: !running`. Up to one poll interval of tail
  // data (the last finding written right at completion) could be missing
  // from what the UI already calls "the complete list".
  it("refetches findings once the scan transitions to completed", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    let scanCalls = 0;
    vi.mocked(getScan).mockImplementation(async () => {
      scanCalls += 1;
      return scanCalls === 1 ? { ...SCAN, status: "running", finished_at: null } : SCAN;
    });
    let findingsCalls = 0;
    vi.mocked(listFindings).mockImplementation(async () => {
      findingsCalls += 1;
      // The "final" finding only exists from the second call onward - as
      // if it were written right at the moment the scan completed.
      return findingsCalls === 1 ? [] : [CRITICAL];
    });
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei")]);
    vi.mocked(listReports).mockResolvedValue([]);

    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/scans/scan-1"]}>
          <Routes>
            <Route path="/scans/:id" element={<ScanDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await vi.waitFor(() => expect(screen.getByText("Escaneo en curso")).toBeInTheDocument());
    expect(findingsCalls).toBe(1);

    // Advance past scanQuery's poll interval so it picks up the
    // now-completed status, which should trigger the extra
    // tasksQuery/findingsQuery fetch under test.
    await vi.advanceTimersByTimeAsync(2500);

    await vi.waitFor(() => expect(findingsCalls).toBeGreaterThan(1));
    await vi.waitFor(() => expect(screen.getByText("Apache Struts RCE")).toBeInTheDocument());
  });
});

describe("ScanDetailPage — a background poll failing after data already loaded", () => {
  // 7th independent evaluation: `if (scanQuery.error) return <ErrorBanner/>`
  // used to be checked before `if (!scan) return null` — since TanStack
  // Query never clears `data` on a failed background refetch, a single
  // transient error during the 4-6 minute polling window blanked out the
  // whole page. It must instead keep showing the already-loaded scan plus
  // an inline error banner.
  beforeEach(() => {
    vi.mocked(listScanTasks).mockResolvedValue([task("t-nuclei", "nuclei")]);
    vi.mocked(listFindings).mockResolvedValue([CRITICAL]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  it("keeps showing the already-loaded scan instead of blanking out", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    vi.mocked(getScan).mockResolvedValueOnce(SCAN);

    renderPage(queryClient);
    await screen.findByText("Apache Struts RCE");

    vi.mocked(getScan).mockRejectedValueOnce(new Error("network error"));
    await queryClient.refetchQueries({ queryKey: ["scan", "scan-1"] });

    expect(screen.getByText("Apache Struts RCE")).toBeInTheDocument();
    expect(await screen.findByText("No se pudo contactar al backend")).toBeInTheDocument();
  });
});

describe("ScanDetailPage — a background poll failing on tasksQuery after data already loaded", () => {
  // 8th independent evaluation: the same error-before-data bug fixed for
  // scanQuery in the block above was still present in this page's own
  // tasksQuery, one query lower in the same component - `tasksQuery.error
  // ? <ErrorBanner/> : <ToolTimeline/>` hid the whole tool timeline (still
  // fully populated from cached data) on a single transient poll failure.
  beforeEach(() => {
    vi.mocked(getScan).mockResolvedValue(SCAN);
    vi.mocked(listFindings).mockResolvedValue([CRITICAL]);
    vi.mocked(listReports).mockResolvedValue([]);
  });

  it("keeps showing the tool timeline instead of blanking it out", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    vi.mocked(listScanTasks).mockResolvedValueOnce([task("t-nuclei", "nuclei")]);

    renderPage(queryClient);
    await screen.findByText("Apache Struts RCE");
    expect(screen.getAllByText("Nuclei").length).toBeGreaterThan(0);

    vi.mocked(listScanTasks).mockRejectedValueOnce(new Error("network error"));
    await queryClient.refetchQueries({ queryKey: ["scan-tasks", "scan-1"] });

    expect(screen.getAllByText("Nuclei").length).toBeGreaterThan(0);
    expect(await screen.findByText("No se pudo contactar al backend")).toBeInTheDocument();
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
