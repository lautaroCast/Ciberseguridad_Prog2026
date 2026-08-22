export function Skeleton({ width, height = 10 }: { width: number | string; height?: number }) {
  return <span className="skeleton" style={{ display: "block", width, height }} />;
}

/** Placeholder rows shaped like the table they replace. */
export function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="tbl" role="status" aria-label="Cargando">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="tbl__row">
          <Skeleton width={84} />
          <Skeleton width={index % 2 === 0 ? 240 : 180} />
          <div style={{ flexGrow: 1 }} />
          <Skeleton width={62} />
        </div>
      ))}
    </div>
  );
}
