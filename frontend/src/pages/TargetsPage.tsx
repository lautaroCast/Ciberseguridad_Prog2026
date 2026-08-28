import { useState } from "react";
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { createTarget, listScansForTarget, listTargets } from "../api";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { AlertIcon, SpinnerIcon } from "../components/Icon";
import { TableSkeleton } from "../components/Skeleton";
import { StatusIcon } from "../components/StatusIcon";
import { statusColor, statusLabel } from "../lib/status";
import { formatDateTime } from "../lib/format";
import { isTerminalStatus } from "../api/scans";
import type { ScanRead, TargetRead } from "../types";

/**
 * Mirrors the backend's `BACKEND_ALLOWED_LAB_HOSTS` whitelist.
 *
 * Only these hosts can ever be registered — anything else is rejected
 * server-side with a 422. Offering a free-text field that fails after
 * submission would be the wrong affordance, so the constraint is built
 * into the control instead.
 */
const LAB_HOSTS = (import.meta.env.VITE_LAB_HOSTS ?? "juice-shop,dvwa")
  .split(",")
  .map((host: string) => host.trim())
  .filter(Boolean);

function lastScanOf(scans: ScanRead[] | undefined): ScanRead | null {
  if (!scans || scans.length === 0) return null;
  return [...scans].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )[0];
}

export function TargetsPage() {
  const queryClient = useQueryClient();
  const targetsQuery = useQuery({ queryKey: ["targets"], queryFn: () => listTargets() });

  const [name, setName] = useState("");
  const [host, setHost] = useState(LAB_HOSTS[0] ?? "");
  const [description, setDescription] = useState("");

  const targets = targetsQuery.data ?? [];

  // One scan-history request per target. With a two-host whitelist this is
  // two requests, not a scale problem worth a dedicated endpoint.
  const scanQueries = useQueries({
    queries: targets.map((target) => ({
      queryKey: ["target-scans", target.id],
      queryFn: () => listScansForTarget(target.id),
      refetchInterval: (query: { state: { data?: ScanRead[] } }) => {
        const latest = lastScanOf(query.state.data);
        return latest && !isTerminalStatus(latest.status) ? 4000 : false;
      },
    })),
  });

  const createMutation = useMutation({
    mutationFn: () => createTarget({ name, host, description: description || null }),
    onSuccess: () => {
      setName("");
      setDescription("");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
    },
  });

  return (
    <div>
      <div className="row" style={{ gap: 12, alignItems: "baseline", marginBottom: 4 }}>
        <h1>Objetivos</h1>
        <span style={{ fontSize: 13, color: "var(--ink-3)" }}>
          {targets.length} {targets.length === 1 ? "registrado" : "registrados"}
        </span>
      </div>
      <p style={{ margin: "0 0 22px", fontSize: 13, color: "var(--ink-2)", maxWidth: 640 }}>
        Aplicaciones del laboratorio habilitadas para escaneo. La whitelist del servidor define qué
        hosts pueden registrarse.
      </p>

      <form
        className="panel"
        style={{ padding: "16px 18px 18px", marginBottom: 26 }}
        onSubmit={(event) => {
          event.preventDefault();
          createMutation.mutate();
        }}
      >
        <div className="th" style={{ marginBottom: 14 }}>
          Registrar objetivo
        </div>
        <div className="row" style={{ gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div className="field" style={{ width: 210 }}>
            <label className="field__label" htmlFor="target-name">
              Nombre
            </label>
            <input
              id="target-name"
              className="input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="p. ej. DVWA local"
              required
            />
          </div>

          <div className="field">
            <span className="field__label" id="host-label">
              Host
            </span>
            <div className="segmented" role="group" aria-labelledby="host-label">
              {LAB_HOSTS.map((option: string) => (
                <button
                  key={option}
                  type="button"
                  className="segmented__option"
                  aria-pressed={host === option}
                  onClick={() => setHost(option)}
                >
                  {option}
                </button>
              ))}
            </div>
            <span className="field__hint">Únicos hosts habilitados por la whitelist</span>
          </div>

          <div className="field" style={{ flexGrow: 1, minWidth: 220 }}>
            <label className="field__label" htmlFor="target-desc">
              Descripción <span style={{ color: "var(--ink-3)" }}>opcional</span>
            </label>
            <input
              id="target-desc"
              className="input"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn btn--primary"
            style={{ marginTop: 24 }}
            disabled={createMutation.isPending || !name.trim()}
          >
            {createMutation.isPending && <SpinnerIcon size={12} />}
            Registrar
          </button>
        </div>
      </form>

      <ErrorBanner error={createMutation.error} />
      <ErrorBanner error={targetsQuery.error} />

      {targetsQuery.isLoading && <TableSkeleton />}

      {targetsQuery.data && targets.length === 0 && (
        <div className="tbl">
          <EmptyState title="Todavía no hay objetivos registrados">
            Registrá{" "}
            {LAB_HOSTS.map((option: string, index: number) => (
              <span key={option}>
                {index > 0 && " o "}
                <span className="mono">{option}</span>
              </span>
            ))}{" "}
            para empezar. Son los únicos hosts habilitados por la whitelist del laboratorio.
          </EmptyState>
        </div>
      )}

      {targets.length > 0 && (
        <div className="tbl" role="table" aria-label="Objetivos registrados">
          <div className="tbl__head" role="row">
            <span className="th" role="columnheader" style={{ flexGrow: 1 }}>
              Nombre
            </span>
            <span className="th" role="columnheader" style={{ width: 120, flexShrink: 0 }}>
              Host
            </span>
            <span className="th" role="columnheader" style={{ width: 96, flexShrink: 0 }}>
              Estado
            </span>
            <span className="th" role="columnheader" style={{ width: 190, flexShrink: 0 }}>
              Último escaneo
            </span>
            <span className="th" role="columnheader" style={{ width: 92, flexShrink: 0 }} />
          </div>

          {targets.map((target: TargetRead, index: number) => {
            const scanQuery = scanQueries[index];
            const scans = scanQuery?.data;
            const latest = lastScanOf(scans);
            const running = latest ? !isTerminalStatus(latest.status) : false;
            // Never loaded at all (as opposed to a later background poll
            // failing) is the only case with no cached data to fall back
            // on - a transient poll error after data already loaded must
            // not hide an already-known last-scan link.
            const scanHistoryNeverLoaded = !scans && Boolean(scanQuery?.error);

            return (
              <div key={target.id} className="tbl__row" role="row">
                <div role="cell" style={{ flexGrow: 1 }}>
                  <Link to={`/targets/${target.id}`} style={{ fontWeight: 500 }}>
                    {target.name}
                  </Link>
                  {target.description && (
                    <div style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 2 }}>
                      {target.description}
                    </div>
                  )}
                </div>

                <span
                  role="cell"
                  className="mono"
                  style={{ width: 120, flexShrink: 0, fontSize: 12, color: "var(--ink-2)" }}
                >
                  {target.host}
                </span>

                <span
                  role="cell"
                  className="row"
                  style={{ width: 96, flexShrink: 0, gap: 5, fontSize: 12, color: "var(--ink-2)" }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: target.is_active ? "var(--ok)" : "var(--ink-3)",
                    }}
                  />
                  {target.is_active ? "activo" : "inactivo"}
                </span>

                <span role="cell" style={{ width: 190, flexShrink: 0, fontSize: 12, color: "var(--ink-2)" }}>
                  {scanHistoryNeverLoaded && (
                    <span className="row" style={{ gap: 5, color: "var(--bad)" }}>
                      <AlertIcon size={12} />
                      no se pudo cargar
                    </span>
                  )}
                  {!scanHistoryNeverLoaded && !latest && (
                    <span style={{ color: "var(--ink-3)" }}>nunca escaneado</span>
                  )}
                  {!scanHistoryNeverLoaded && latest && (
                    <Link
                      to={`/scans/${latest.id}`}
                      className="row"
                      style={{ gap: 6, color: running ? "var(--accent)" : statusColor(latest.status) }}
                    >
                      <StatusIcon status={latest.status} size={12} />
                      <span style={{ color: "var(--ink-2)" }}>
                        {running ? statusLabel(latest.status) : formatDateTime(latest.created_at)}
                      </span>
                    </Link>
                  )}
                </span>

                <span role="cell" style={{ width: 92, flexShrink: 0, textAlign: "right" }}>
                  <Link to={`/targets/${target.id}`} className="btn">
                    Ver detalle
                  </Link>
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
