#!/usr/bin/env bash
# Alembic's contract is append-only: once a migration file has been
# merged, a database that already applied it will never re-run it, so an
# in-place edit silently diverges from what every already-bootstrapped
# database actually has. This exact bug orphaned a `users` table/
# `user_role` enum for ~10 days on the real dev database, undetected,
# until found by hand (see database/migrations/versions/
# e0fd682ed5c0_drop_unused_users_table.py's own docstring). CI already
# runs the real migration chain from an empty schema on every run
# (`docker compose up -d migrate` in unit-tests) - but that can never
# catch this specific class of bug, because it only manifests on a
# database that isn't fresh. Only a diff against history can catch it.
set -euo pipefail

BASE_SHA="${1:?usage: check-migration-immutability.sh <base-sha>}"

if [ -z "$BASE_SHA" ] || ! git cat-file -e "${BASE_SHA}^{commit}" 2>/dev/null; then
  echo "No usable base commit ($BASE_SHA) - nothing to diff against, skipping."
  exit 0
fi

changed=$(git diff --name-status "$BASE_SHA" HEAD -- database/migrations/versions/ | grep -v '^A' || true)

if [ -n "$changed" ]; then
  echo "ERROR: an already-existing migration file was modified or removed:"
  echo "$changed"
  echo
  echo "Alembic migrations are append-only once merged - add a new migration instead of editing an existing one."
  exit 1
fi

echo "OK - no existing migration file under database/migrations/versions/ was modified."
