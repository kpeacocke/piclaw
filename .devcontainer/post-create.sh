#!/usr/bin/env bash
set -euo pipefail

export PATH="/home/vscode/.local/bin:$PATH"

SUDO=""
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
fi

echo "[devcontainer] Installing Python project dependencies"
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

echo "[devcontainer] Upgrading npm to latest"
npm install -g npm@latest

echo "[devcontainer] Installing Ansible collections"
ansible-galaxy collection install -r collections/requirements.yml

echo "[devcontainer] Installing pre-commit hooks"
pre-commit install

if ! command -v snyk >/dev/null 2>&1; then
  echo "[devcontainer] Installing Snyk CLI"
  npm install -g snyk
else
  echo "[devcontainer] Snyk CLI already installed"
fi

if ! command -v sonar-scanner >/dev/null 2>&1; then
  echo "[devcontainer] Installing sonar-scanner CLI"
  SCANNER_VERSION="6.2.1.4610"
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64)
      SCANNER_ARCH="linux-x64"
      ;;
    aarch64|arm64)
      SCANNER_ARCH="linux-aarch64"
      ;;
    *)
      echo "[devcontainer] Unsupported architecture for sonar-scanner: $ARCH"
      exit 1
      ;;
  esac

  SCANNER_ZIP="sonar-scanner-cli-${SCANNER_VERSION}-${SCANNER_ARCH}.zip"
  SCANNER_URL="https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/${SCANNER_ZIP}"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$SCANNER_URL" -o "/tmp/${SCANNER_ZIP}"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$SCANNER_URL" -O "/tmp/${SCANNER_ZIP}"
  else
    echo "[devcontainer] Neither curl nor wget is available to download sonar-scanner"
    exit 1
  fi

  python3 - <<PY
import zipfile
zipfile.ZipFile('/tmp/${SCANNER_ZIP}').extractall('/tmp')
PY

  chmod +x "/tmp/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}/bin/sonar-scanner"
  chmod +x "/tmp/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}/jre/bin/java"

  ${SUDO} rm -rf "/opt/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}"
  ${SUDO} mv "/tmp/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}" /opt/
  ${SUDO} ln -sf "/opt/sonar-scanner-${SCANNER_VERSION}-${SCANNER_ARCH}/bin/sonar-scanner" /usr/local/bin/sonar-scanner
fi

echo "[devcontainer] Tool versions"
python --version
gh --version | head -n 1
ansible --version | head -n 1
ansible-lint --version | head -n 1
molecule --version | head -n 1
pytest --version
snyk --version
sonar-scanner --version | head -n 1
