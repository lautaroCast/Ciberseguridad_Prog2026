import { ApiError } from "../api/client";

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof ApiError ? error.detail : "Ocurrió un error inesperado.";
  return <div className="error-banner">{message}</div>;
}
