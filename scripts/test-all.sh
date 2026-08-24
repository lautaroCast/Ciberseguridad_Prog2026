#!/usr/bin/env bash
# Runs the pytest suite for each VulnScan microservice inside its own
# already-running Docker container — nothing is installed on the host.
set -e
for svc in backend scanner reports; do
  echo "== $svc =="
  docker compose exec "$svc" pytest
done

# scripts/ground_truth/match_findings.py computes the actual recall/
# precision numbers the thesis reports (§12.5/Anexo E) — outside
# backend/tests' own discovery path (pytest.ini scopes to tests/), so it
# needs its own explicit run rather than silently never being exercised.
echo "== scripts/ground_truth (match_findings.py) =="
docker compose exec backend pytest scripts/ground_truth/test_match_findings.py
