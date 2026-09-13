/**
 * True only when a query never loaded data and ended in error — not while
 * it's still loading, and not when it succeeded with an empty/falsy
 * result (an empty list is real data, not "didn't load").
 */
export function queryFailedToLoad(query: { data: unknown; error: unknown }): boolean {
  return query.data === undefined && Boolean(query.error);
}
