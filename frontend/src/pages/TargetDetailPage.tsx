import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getTarget, listScansForTarget, triggerPipeline } from "../api";
import { ErrorBanner } from "../components/ErrorBanner";
import { Spinner } from "../components/Spinner";
import { StatusBadge } from "../components/StatusBadge";

export function TargetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const targetId = id!;
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const targetQuery = useQuery({
    queryKey: ["target", targetId],
    queryFn: () => getTarget(targetId),
  });

  const scansQuery = useQuery({
    queryKey: ["target-scans", targetId],
    queryFn: () => listScansForTarget(targetId),
  });

  const triggerPipelineMutation = useMutation({
    mutationFn: () => triggerPipeline(targetId),
    onSuccess: (scan) => {
      queryClient.invalidateQueries({ queryKey: ["target-scans", targetId] });
      navigate(`/scans/${scan.id}`);
    },
  });

  if (targetQuery.isLoading) return <Spinner />;
  if (targetQuery.error) return <ErrorBanner error={targetQuery.error} />;
  const target = targetQuery.data;
  if (!target) return null;

  return (
    <div>
      <p>
        <Link to="/targets">&larr; Volver a targets</Link>
      </p>
      <h1>{target.name}</h1>
      <dl className="target-detail">
        <dt>Host</dt>
        <dd>{target.host}</dd>
        <dt>Descripción</dt>
        <dd>{target.description ?? "-"}</dd>
        <dt>Estado</dt>
        <dd>{target.is_active ? "Activo" : "Inactivo"}</dd>
      </dl>

      <div className="actions">
        <button
          type="button"
          onClick={() => triggerPipelineMutation.mutate()}
          disabled={triggerPipelineMutation.isPending}
        >
          Correr Pipeline
        </button>
      </div>
      <ErrorBanner error={triggerPipelineMutation.error} />

      <h2>Historial de scans</h2>
      {scansQuery.isLoading && <Spinner />}
      <ErrorBanner error={scansQuery.error} />
      {scansQuery.data && scansQuery.data.length === 0 && <p>Todavía no hay scans para este target.</p>}
      {scansQuery.data && scansQuery.data.length > 0 && (
        <ul className="scan-history">
          {scansQuery.data.map((scan) => (
            <li key={scan.id}>
              <Link to={`/scans/${scan.id}`}>{new Date(scan.created_at).toLocaleString()}</Link>{" "}
              <StatusBadge status={scan.status} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
