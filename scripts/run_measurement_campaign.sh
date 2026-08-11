#!/usr/bin/env bash
# Runs scripts/measurement_campaign.py inside the Backend container, first
# capturing host-only facts the container itself can't see (audit A-11: the
# thesis's §9.4 host-spec table, and `docker --version`/`docker compose
# version`) and passing them through as env vars. Optional: TARGET_HOST/RUNS,
# same as the script itself.
set -e

if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* ]]; then
  HOST_CPU="$(powershell -NoProfile -Command '(Get-CimInstance Win32_Processor).Name' | sed 's/[[:space:]]*$//')"
  HOST_RAM_GB="$(powershell -NoProfile -Command '[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)' | tr ',' '.')"
  HOST_DISK_GB="$(powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='C:'\").Size / 1GB, 1)" | tr ',' '.')"
  HOST_OS_CAPTION="$(powershell -NoProfile -Command '(Get-CimInstance Win32_OperatingSystem).Caption')"
  HOST_OS_VERSION="$(powershell -NoProfile -Command '(Get-CimInstance Win32_OperatingSystem).Version')"
  HOST_OS="$HOST_OS_CAPTION $HOST_OS_VERSION"
else
  HOST_CPU="$(lscpu | awk -F: '/Model name/ {gsub(/^ +/, "", $2); print $2}')"
  HOST_RAM_GB="$(free -g | awk '/Mem:/ {print $2}')"
  HOST_DISK_GB="$(df -BG / | awk 'NR==2 {gsub(/G/, "", $2); print $2}')"
  HOST_OS="$(uname -sr)"
fi

# Scanner tool versions come from the live Scanner container itself
# (audit A-12) — nmap/whatweb/nikto respond to a plain flag; nuclei needs
# two separate calls for engine vs. template-set version; zap.sh prints its
# banner (with the version) to stderr on startup, so grep it out of there.
export MSYS_NO_PATHCONV=1
HOST_NMAP_VERSION="$(docker compose exec -T scanner nmap --version 2>&1 | head -1)"
HOST_WHATWEB_VERSION="$(docker compose exec -T scanner whatweb --version 2>&1 | head -1)"
HOST_NIKTO_VERSION="$(docker compose exec -T scanner /opt/nikto/program/nikto.pl -Version 2>&1 | head -1)"
HOST_NUCLEI_VERSION="$(docker compose exec -T scanner nuclei -version 2>&1 | grep -i 'Engine Version' | sed 's/.*Engine Version: //')"
HOST_NUCLEI_TEMPLATES_VERSION="$(docker compose exec -T scanner nuclei -tv 2>&1 | grep -i 'templates version' | sed 's/.*templates version: //')"
HOST_ZAP_VERSION="$(docker compose exec -T scanner zap.sh -version 2>&1 | tail -1)"

docker compose exec -T \
  -e HOST_DOCKER_VERSION="$(docker --version)" \
  -e HOST_DOCKER_COMPOSE_VERSION="$(docker compose version)" \
  -e HOST_CPU="$HOST_CPU" \
  -e HOST_RAM_GB="$HOST_RAM_GB" \
  -e HOST_DISK_GB="$HOST_DISK_GB" \
  -e HOST_OS="$HOST_OS" \
  -e HOST_NMAP_VERSION="$HOST_NMAP_VERSION" \
  -e HOST_WHATWEB_VERSION="$HOST_WHATWEB_VERSION" \
  -e HOST_NIKTO_VERSION="$HOST_NIKTO_VERSION" \
  -e HOST_NUCLEI_VERSION="$HOST_NUCLEI_VERSION" \
  -e HOST_NUCLEI_TEMPLATES_VERSION="$HOST_NUCLEI_TEMPLATES_VERSION" \
  -e HOST_ZAP_VERSION="$HOST_ZAP_VERSION" \
  ${TARGET_HOST:+-e TARGET_HOST="$TARGET_HOST"} \
  ${RUNS:+-e RUNS="$RUNS"} \
  backend python scripts/measurement_campaign.py
