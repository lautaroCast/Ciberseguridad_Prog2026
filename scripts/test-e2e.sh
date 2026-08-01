#!/usr/bin/env bash
# Runs the real, slow, end-to-end pipeline test (scripts/integration_test.py)
# inside the already-running Backend container. Unlike test-all.sh, this
# needs the full stack up (db, backend, scanner, reports, n8n, dvwa) and
# takes several minutes — see docs/security.md and the Módulo 9 plan for
# why this is manual/on-demand rather than part of the fast test suite.
set -e
docker compose exec backend python scripts/integration_test.py
