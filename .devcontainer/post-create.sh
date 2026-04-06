#!/usr/bin/env bash
set -euo pipefail

export PATH="/home/vscode/.local/bin:$PATH"

SUDO=""
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
fi

STATE_DIR="${HOME}/.cache/piclaw-devcontainer"
STATE_FILE="${STATE_DIR}/bootstrap.sha256"
mkdir -p "${STATE_DIR}"

# Re-run expensive setup only when bootstrap inputs change.
BOOTSTRAP_HASH="$({
  printf '%s\n' 'post-create-v6'
  cat requirements-dev.txt
  cat requirements-dev.lock
} | sha256sum | awk '{print $1}')"

BOOTSTRAP_NEEDED="true"
if [[ -f "${STATE_FILE}" ]] && [[ "$(cat "${STATE_FILE}")" == "${BOOTSTRAP_HASH}" ]]; then
  BOOTSTRAP_NEEDED="false"
fi

# Required by Snyk and other tools that read a machine identifier
if [[ ! -f /etc/machine-id ]]; then
  ${SUDO} sh -c 'cat /proc/sys/kernel/random/uuid | tr -d "-" > /etc/machine-id'
fi

if [[ "${BOOTSTRAP_NEEDED}" == "true" ]]; then
  echo "[devcontainer] Running lightweight workspace bootstrap"

  echo "[devcontainer] Creating workspace venv and installing dev dependencies"
  python3 -m venv .venv
  .venv/bin/pip install --require-hashes -r requirements-dev.lock

  echo "[devcontainer] Installing pre-commit hooks"
  pre-commit install
else
  echo "[devcontainer] Workspace bootstrap already up to date; skipping"
fi

if [[ "${BOOTSTRAP_NEEDED}" == "true" ]]; then
  echo "${BOOTSTRAP_HASH}" > "${STATE_FILE}"
fi

echo "[devcontainer] Tool versions"
python --version
gh --version | head -n 1
ansible --version | head -n 1
ansible-lint --version | head -n 1
molecule --version | head -n 1
pytest --version
sonar-scanner --version | head -n 1
