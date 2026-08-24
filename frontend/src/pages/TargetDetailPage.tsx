import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteTarget,
  getTarget,
  isTerminalStatus,
  listScansForTarget,
  triggerPipeline,
  updateTarget,
} from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { ClockIcon, PlayIcon, SpinnerIcon } from "../components/Icon";
import { Crumbs } from "../components/Layout";
import { TableSkeleton } from "../components/Skeleton";
import { StatusIcon } from "../components/StatusIcon";
import { statusColor, statusLabel } from "../lib/status";
import { elapsedSeconds, formatDateTime, formatDuration } from "../lib/format";
import type { ScanRead } from "../types";

export function TargetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const targetId = id!;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const targetQuery = useQuery({
    queryKey: ["target", targetId],
    queryFn: () => getTarget(targetId),
  });

  const scansQuery = useQuery({
    queryKey: ["target-scans", targetId],
    queryFn: () => listScansForTarget(targetId),
    refetchInterval: (query) => {
      const scans = query.state.data ?? [];
      return scans.some((scan: ScanRead) => !isTerminalStatus(scan.status)) ? 4000 : false;
    },
  });

  const pipelineMutation = useMutation({
    mutationFn: () => triggerPipeline(targetId),
    onSuccess: (scan) => {
      queryClient.invalidateQueries({ queryKey: ["target-scans", targetId] });
      navigate(`/scans/${scan.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteTarget(targetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      navigate("/targets");
    },
  });

  const updateActiveMutation = useMutation({
    mutationFn: (isActive: boolean) => updateTarget(targetId, { is_active: isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["target", targetId] });
      queryClient.invalidateQueries({ queryKey: ["targets"] });
    },
  });

  if (targetQuery.isLoading) return <TableSkeleton rows={3} />;
  if (targetQuery.error) return <ErrorBanner error={targetQuery.error} />;
  const target = targetQuery.data;
  if (!target) return null;

  const scans = scansQuery.data ?? [];

  return (
    <div>
      <Crumbs items={[{ label: "Objetivos", to: "/targets" }, { label: target.name }]} />

      <div className="row" style={{ gap: 20, alignItems: "flex-start", marginBottom: 26 }}>
        <div style={{ flexGrow: 1 }}>
          <div className="row" style={{ gap: 10, marginBottom: 6 }}>
            <h1>{target.name}</h1>
            <span
              className="row"
              style={{
                gap: 5,
                fontSize: 12,
                color: "var(--ink-2)",
                border: "1px solid var(--line)",
                borderRadius: "var(--radius-chip)",
                padding: "2px 8px",
              }}
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
            <button
              type="button"
              className="btn"
              style={{ fontSize: 11, padding: "2px 8px" }}
              onClick={() => updateActiveMutation.mutate(!target.is_active)}
              disabled={updateActiveMutation.isPending}
            >
              {updateActiveMutation.isPending ? (
                <SpinnerIcon size={11} />
              ) : target.is_active ? (
                "Desactivar"
              ) : (
                "Reactivar"
              )}
            </button>
          </div>
          {target.description && (
            <p style={{ margin: 0, fontSize: 13, color: "var(--ink-2)" }}>{target.description}</p>
          )}
        </div>
        <button
          type="button"
          className="btn btn--danger-quiet"
          onClick={() => setConfirmingDelete(true)}
          disabled={scansQuery.isLoading}
          title={scansQuery.isLoading ? "Cargando historial de escaneos…" : undefined}
        >
          Eliminar
        </button>
      </div>

      <ErrorBanner error={pipelineMutation.error} />
      <ErrorBanner error={deleteMutation.error} />
      <ErrorBanner error={updateActiveMutation.error} />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: 20,
          marginBottom: 28,
        }}
      >
        <div className="panel" style={{ padding: "16px 18px" }}>
          <div className="th" style={{ marginBottom: 13 }}>
            Datos del objetivo
          </div>
          <dl
            style={{
              display: "grid",
              gridTemplateColumns: "108px 1fr",
              gap: "9px 14px",
              fontSize: 12,
              margin: 0,
            }}
          >
            <dt style={{ color: "var(--ink-3)" }}>Host</dt>
            <dd className="mono" style={{ margin: 0 }}>
              {target.host}
            </dd>
            <dt style={{ color: "var(--ink-3)" }}>Laboratorio</dt>
            <dd style={{ margin: 0 }}>{target.is_lab_target ? "sí — en whitelist" : "no"}</dd>
            <dt style={{ color: "var(--ink-3)" }}>Identificador</dt>
            <dd
              className="mono"
              style={{ margin: 0, color: "var(--ink-2)", overflowWrap: "anywhere" }}
            >
              {target.id}
            </dd>
            <dt style={{ color: "var(--ink-3)" }}>Registrado</dt>
            <dd style={{ margin: 0 }}>{formatDateTime(target.created_at)}</dd>
          </dl>
        </div>

        <div className="callout callout--accent stack" style={{ padding: "16px 18px", gap: 0 }}>
          <div className="th" style={{ marginBottom: 8 }}>
            Ejecutar pipeline
          </div>
          <p style={{ margin: "0 0 14px", fontSize: 12, lineHeight: 1.6, color: "var(--ink-2)" }}>
            Lanza las doce etapas contra <span className="mono">{target.host}</span>:
            reconocimiento, fingerprinting, escaneo con las cinco herramientas, normalización y
            persistencia.
          </p>
          <div
            className="row"
            style={{ gap: 9, marginBottom: 15, fontSize: 12, color: "var(--ink-2)" }}
          >
            <span style={{ color: "var(--warn)", display: "flex", flexShrink: 0 }}>
              <ClockIcon />
            </span>
            <span>
              Tarda entre <strong style={{ color: "var(--ink)" }}>4 y 6 minutos</strong>. Podés
              cerrar la pestaña — sigue en segundo plano.
            </span>
          </div>
          <div style={{ flexGrow: 1 }} />
          <button
            type="button"
            className="btn btn--primary btn--lg"
            style={{ alignSelf: "flex-start" }}
            onClick={() => pipelineMutation.mutate()}
            disabled={pipelineMutation.isPending || !target.is_active}
          >
            {pipelineMutation.isPending ? <SpinnerIcon size={13} /> : <PlayIcon />}
            Correr pipeline
          </button>
        </div>
      </div>

      <div className="row" style={{ gap: 11, alignItems: "baseline", marginBottom: 12 }}>
        <span className="th">Historial de escaneos</span>
        <span style={{ fontSize: 12, color: "var(--ink-3)" }}>
          {scans.length} {scans.length === 1 ? "ejecución" : "ejecuciones"}
        </span>
      </div>

      <ErrorBanner error={scansQuery.error} />
      {scansQuery.isLoading && <TableSkeleton />}

      {scansQuery.data && scans.length === 0 && (
        <div className="tbl">
          <EmptyState
            title="Este objetivo nunca se escaneó"
            action={
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => pipelineMutation.mutate()}
                disabled={pipelineMutation.isPending || !target.is_active}
              >
                Correr pipeline
              </button>
            }
          >
            {target.is_active
              ? "El objetivo está registrado y activo, pero no tiene historial. Corré el pipeline para generar el primero."
              : "El objetivo está registrado pero inactivo, y no tiene historial. Reactivalo arriba para poder correr el pipeline."}
          </EmptyState>
        </div>
      )}

      {scans.length > 0 && (
        <div className="tbl" role="table" aria-label="Historial de escaneos">
          <div className="tbl__head" role="row">
            <span className="th" role="columnheader" style={{ width: 118, flexShrink: 0 }}>
              Estado
            </span>
            <span className="th" role="columnheader" style={{ width: 152, flexShrink: 0 }}>
              Inicio
            </span>
            <span className="th" role="columnheader" style={{ width: 74, flexShrink: 0 }}>
              Duración
            </span>
            <span className="th" role="columnheader" style={{ flexGrow: 1 }}>
              Detalle
            </span>
          </div>

          {scans.map((scan) => {
            const seconds = elapsedSeconds(scan.started_at, scan.finished_at);
            return (
              <Link
                key={scan.id}
                to={`/scans/${scan.id}`}
                className="tbl__row"
                role="row"
                style={{ color: "inherit", textDecoration: "none" }}
              >
                <span
                  role="cell"
                  className="row"
                  style={{ width: 118, flexShrink: 0, gap: 7, color: statusColor(scan.status) }}
                >
                  <StatusIcon status={scan.status} size={13} />
                  <span style={{ fontSize: 12, fontWeight: 500 }}>{statusLabel(scan.status)}</span>
                </span>
                <span
                  role="cell"
                  className="mono"
                  style={{ width: 152, flexShrink: 0, fontSize: 12, color: "var(--ink-2)" }}
                >
                  {formatDateTime(scan.created_at)}
                </span>
                <span
                  role="cell"
                  className="mono"
                  style={{ width: 74, flexShrink: 0, fontSize: 12, color: "var(--ink-2)" }}
                >
                  {seconds === null ? "—" : formatDuration(seconds)}
                </span>
                <span role="cell" style={{ flexGrow: 1, fontSize: 12, color: "var(--ink-3)" }}>
                  {scan.error_message ?? "—"}
                </span>
              </Link>
            );
          })}
        </div>
      )}

      {confirmingDelete && (
        <ConfirmDialog
          title={`¿Eliminar el objetivo ${target.name}?`}
          confirmLabel="Eliminar todo"
          pending={deleteMutation.isPending}
          onCancel={() => setConfirmingDelete(false)}
          onConfirm={() => deleteMutation.mutate()}
        >
          <p style={{ margin: "0 0 8px" }}>
            {scansQuery.isError ? (
              <>
                No se pudo confirmar el historial real de este objetivo (falló la carga). Se
                borran también{" "}
                <strong style={{ color: "var(--ink)" }}>
                  todos sus escaneos, hallazgos y reportes generados, sean los que sean
                </strong>
                . La operación no se puede deshacer.
              </>
            ) : (
              <>
                Se borran también{" "}
                <strong style={{ color: "var(--ink)" }}>
                  sus {scans.length} {scans.length === 1 ? "escaneo" : "escaneos"}, todos sus
                  hallazgos y todos sus reportes generados
                </strong>
                . La operación no se puede deshacer.
              </>
            )}
          </p>
          <span style={{ fontSize: 11, color: "var(--ink-3)" }}>
            El borrado en cascada lo hace la base de datos; el dashboard no conserva copia.
          </span>
        </ConfirmDialog>
      )}
    </div>
  );
}
