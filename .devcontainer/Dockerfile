FROM mcr.microsoft.com/devcontainers/python@sha256:de0e677fbf35384da5c723ab101ba8f03af95f1f29d5e4134ecb021dc7e96dd1

USER 0:0

# Provide clipboard helpers needed by tools like Snyk in terminal sessions.
RUN set -eux; \
  rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.list.save; \
  sed -i \
    -e 's|http://deb.debian.org/debian-security|https://snapshot.debian.org/archive/debian-security/20260316T000000Z|' \
    -e 's|http://deb.debian.org/debian|https://snapshot.debian.org/archive/debian/20260316T000000Z|' \
    /etc/apt/sources.list.d/debian.sources; \
  sed -i '/^Signed-By/i Check-Valid-Until: no' /etc/apt/sources.list.d/debian.sources; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    xclip=0.13-4 \
    xsel=1.2.1-1 \
    wl-clipboard=2.2.1-2 \
  ; \
  rm -rf /var/lib/apt/lists/*

# Install SonarScanner CLI once in the image.
ARG SCANNER_VERSION=6.2.1.4610
RUN set -eux; \
    ARCH="$(uname -m)"; \
    case "$ARCH" in \
      x86_64) SCANNER_ARCH="linux-x64" ;; \
      aarch64|arm64) SCANNER_ARCH="linux-aarch64" ;; \
      *) echo "Unsupported architecture for sonar-scanner: $ARCH"; exit 1 ;; \
    esac; \
    SCANNER_ZIP="sonar-scanner-cli-${SCANNER_VERSION}-${SCANNER_ARCH}.zip"; \
    SCANNER_URL="https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/${SCANNER_ZIP}"; \
    curl -fsSL "$SCANNER_URL" -o "/tmp/${SCANNER_ZIP}"; \
    python3 -c "import zipfile; zipfile.ZipFile('/tmp/${SCANNER_ZIP}').extractall('/tmp')"; \
    chmod +x "/tmp/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}/bin/sonar-scanner"; \
    chmod +x "/tmp/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}/jre/bin/java"; \
    rm -rf "/opt/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}"; \
    mv "/tmp/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}" /opt/; \
    ln -sf "/opt/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}/bin/sonar-scanner" /usr/local/bin/sonar-scanner; \
    rm -f "/tmp/${SCANNER_ZIP}"

USER 1000:1000

# Python packages installed as the vscode user land in ~/.local/bin.
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Copy only dependency manifests first to maximize Docker layer cache hits.
COPY --chown=vscode:vscode requirements-dev.txt /tmp/piclaw/requirements-dev.txt
COPY --chown=vscode:vscode requirements-dev.lock /tmp/piclaw/requirements-dev.lock
COPY --chown=vscode:vscode collections/requirements.yml /tmp/piclaw/collections-requirements.yml

RUN set -eux; \
  pip install --no-cache-dir --require-hashes -r /tmp/piclaw/requirements-dev.lock; \
    ansible-galaxy collection install -r /tmp/piclaw/collections-requirements.yml
