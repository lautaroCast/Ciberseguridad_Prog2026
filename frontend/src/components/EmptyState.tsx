import type { ReactNode } from "react";

/**
 * Empty states are written per cause, never as one generic "no data":
 * no targets, no scans and no findings each mean something different and
 * lead to a different next action.
 */
export function EmptyState({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty__title">{title}</div>
      <p className="empty__body">{children}</p>
      {action && <div style={{ marginTop: 15 }}>{action}</div>}
    </div>
  );
}
