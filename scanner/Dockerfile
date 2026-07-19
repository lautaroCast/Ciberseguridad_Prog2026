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
RUN NUCLEI_URL="$(curl -sSL https://api.github.com/repos/projectdiscovery/nuclei/releases/latest \
        | grep -oE '"browser_download_url": *"[^"]*linux_amd64\.zip"' \
        | grep -oE 'https://[^"]*')" \
    && curl -sSL -o /tmp/nuclei.zip "$NUCLEI_URL" \
    && unzip -oq /tmp/nuclei.zip -d /usr/local/bin nuclei \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip \
    && nuclei -update-templates
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

EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
