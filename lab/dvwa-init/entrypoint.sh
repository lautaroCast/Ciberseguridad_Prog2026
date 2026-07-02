#!/bin/sh
# One-shot DVWA database bootstrap.
#
# DVWA ships with an empty database; the tables are normally created by
# opening setup.php in a browser and clicking "Create / Reset Database".
# To keep the platform's "docker compose up -d, no manual steps" contract,
# this script replays that exact request over HTTP: fetch setup.php for a
# session cookie + CSRF token, then POST the same form the button submits.
#
# Safe to run more than once — DVWA's setup routine drops and recreates the
# schema idempotently, which is what we want if the stack is ever restarted
# against a fresh (or stale) database volume.
set -eu

DVWA_URL="${DVWA_URL:-http://dvwa:80}"
COOKIE_JAR="/tmp/dvwa_cookies.txt"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-5}"

log() {
    echo "[dvwa-init] $*"
}

fetch_token() {
    curl -fsS -c "$COOKIE_JAR" -b "$COOKIE_JAR" "${DVWA_URL}/setup.php" -o /tmp/setup.html
    grep -oE "name='user_token' value='[a-f0-9]+'" /tmp/setup.html \
        | sed -E "s/.*value='([a-f0-9]+)'/\1/"
}

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
    token="$(fetch_token || true)"

    if [ -n "$token" ]; then
        curl -fsS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
            --data-urlencode "create_db=Create / Reset Database" \
            --data-urlencode "user_token=${token}" \
            "${DVWA_URL}/setup.php" -o /dev/null

        curl -fsS -b "$COOKIE_JAR" "${DVWA_URL}/setup.php" -o /tmp/result.html

        if grep -q "Setup successful" /tmp/result.html; then
            log "DVWA database initialized successfully."
            exit 0
        fi
    fi

    log "Attempt ${attempt}/${MAX_ATTEMPTS}: DVWA not ready to initialize yet, retrying in ${SLEEP_SECONDS}s..."
    attempt=$((attempt + 1))
    sleep "$SLEEP_SECONDS"
done

log "ERROR: failed to confirm DVWA database initialization after ${MAX_ATTEMPTS} attempts."
exit 1
