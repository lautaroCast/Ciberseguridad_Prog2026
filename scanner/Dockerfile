# Scanner Service — bakes in every tool adapter it drives:
#   - nmap, whatweb: available as Debian packages
#   - nikto: pure-Perl, not packaged for Debian trixie — cloned from source
#   - nuclei: Go binary, not packaged — downloaded from GitHub releases,
#     with templates pre-fetched at build time (a cold `-update-templates`
#     run takes ~1 minute; baking it in means no scan ever pays that cost)
#   - OWASP ZAP: Java, not packaged — downloaded from GitHub releases
#
# Every download resolves "latest" dynamically via the GitHub API rather
# than a hardcoded version, so this Dockerfile doesn't rot as new releases
# ship. All of this was verified by hand against real containers before
# being written here — see the module's README for what was tested.
FROM python:3.12-slim

WORKDIR /app
ENV HOME=/root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        unzip \
        git \
        ca-certificates \
        nmap \
        whatweb \
        libjson-perl \
        libxml-writer-perl \
        libnet-ssleay-perl \
        openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# --- nikto (source checkout, it's a Perl script, no build step) ---------
RUN git clone --depth 1 https://github.com/sullo/nikto /opt/nikto

# --- nuclei (Go binary release) ------------------------------------------
# Template fetch (-update-templates) happens further down, as `appuser`
# with HOME already pointed at its real home — not here as root — so
# build-time and runtime HOME match and nuclei finds the templates it
# baked in, instead of them sitting under /root where a non-root runtime
# user could never see them.
RUN NUCLEI_URL="$(curl -sSL https://api.github.com/repos/projectdiscovery/nuclei/releases/latest \
        | grep -oE '"browser_download_url": *"[^"]*linux_amd64\.zip"' \
        | grep -oE 'https://[^"]*')" \
    && curl -sSL -o /tmp/nuclei.zip "$NUCLEI_URL" \
    && unzip -oq /tmp/nuclei.zip -d /usr/local/bin nuclei \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip
    # NOTE: -duc ("disable update check") must NOT be combined with
    # -update-templates — confirmed by hand while building this module: with
    # both flags together, nuclei silently no-ops (exits 0, prints the
    # banner, never downloads anything) instead of installing templates.
    # -duc is still correct to pass on scan.build_command() calls (see
    # app/adapters/nuclei_adapter.py) where the intent really is "don't
    # phone home during a scan" and no -update-templates is involved.

# --- OWASP ZAP (self-contained Linux tarball) ----------------------------
RUN ZAP_URL="$(curl -sSL https://api.github.com/repos/zaproxy/zaproxy/releases/latest \
        | grep -oE '"browser_download_url": *"[^"]*_Linux\.tar\.gz"' \
        | grep -oE 'https://[^"]*')" \
    && curl -sSL -o /tmp/zap.tar.gz "$ZAP_URL" \
    && mkdir -p /opt/zap \
    && tar -xzf /tmp/zap.tar.gz -C /opt/zap --strip-components=1 \
    && rm /tmp/zap.tar.gz \
    && ln -s /opt/zap/zap.sh /usr/local/bin/zap.sh

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pytest.ini conftest.py ./
COPY tests ./tests

ENV PYTHONPATH=/app

# Least privilege (Módulo 9): nmap loses CAP_NET_RAW under a non-root user
# and auto-falls back from SYN scan (-sS) to TCP connect scan (-sT) — see
# nmap_adapter.py, which doesn't pass -sS explicitly, so this degrades
# gracefully rather than failing. docker-compose.yml re-adds NET_RAW/
# NET_ADMIN anyway to preserve the original scan behavior. ZAP writes
# session/config data under $HOME at scan time, so this container's
# filesystem is deliberately left writable (no read_only) rather than
# guessing every path ZAP/Nikto/Nuclei might touch at runtime.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /opt/nikto /opt/zap /app
ENV HOME=/home/appuser
USER appuser

# `nuclei -update-templates` exits 0 even when it installs nothing.
# Observed on a real build of this image: the step "succeeded", left
# $HOME/nuclei-templates empty, and every scan afterwards failed at
# runtime with "no templates provided for scan" while the image looked
# perfectly healthy and the pipeline reported the scan as completed
# (the n8n nodes run with continueOnFail).
#
# So retry on the OBSERVABLE OUTCOME rather than the exit code — the
# usual cause is a transient network failure or an anonymous GitHub rate
# limit, both of which this Dockerfile is already exposed to twice above
# — and then assert the directory really is populated, so a broken
# template set fails the build instead of shipping a scanner that cannot
# find anything. Nuclei is the only tool in the platform that can emit
# `critical` severity, so silently losing it changes the results.
RUN set -eu; \
    for attempt in 1 2 3; do \
        nuclei -update-templates || true; \
        if [ -n "$(ls -A "$HOME/nuclei-templates" 2>/dev/null)" ]; then break; fi; \
        echo "nuclei templates still empty after attempt $attempt; retrying" >&2; \
        sleep 5; \
    done; \
    if [ -z "$(ls -A "$HOME/nuclei-templates" 2>/dev/null)" ]; then \
        echo "ERROR: nuclei -update-templates installed no templates" >&2; \
        exit 1; \
    fi; \
    nuclei -tv 2>&1 | tail -1 | tee "$HOME/.nuclei-templates-version"

EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
