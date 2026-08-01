#!/usr/bin/env bash
# Runs the pytest suite for each VulnScan microservice inside its own
# already-running Docker container — nothing is installed on the host.
set -e
for svc in backend scanner reports; do
  echo "== $svc =="
  docker compose exec "$svc" pytest
done
