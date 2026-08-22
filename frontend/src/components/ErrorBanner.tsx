import { AlertIcon } from "./Icon";
import { ApiError } from "../api/client";

/**
 * Surfaces the API's own `detail` string rather than a generic message —
 * a 409 (duplicate name) and a 422 (host not whitelisted) need different
 * corrective action from the operator, and only the backend knows which
 * one happened.
 */
export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;

  const isApi = error instanceof ApiError;
  const title = isApi ? `${error.status} · ${error.detail}` : "No se pudo contactar al backend";
  const body = isApi
    ? null
    : "Verificá que el stack esté levantado y que VITE_API_BASE_URL apunte al backend.";

  return (
    <div className="callout callout--bad" role="alert" style={{ marginBottom: 16 }}>
      <span style={{ color: "var(--bad)", flexShrink: 0, marginTop: 1 }}>
        <AlertIcon />
      </span>
      <div>
        <div style={{ fontSize: 12, fontWeight: 500, color: "var(--bad)" }}>{title}</div>
        {body && <div style={{ marginTop: 3 }}>{body}</div>}
      </div>
    </div>
  );
}
