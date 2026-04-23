# Pi 5 + AI HAT+ 2 OpenClaw Stack

[![CI](https://github.com/kpeacocke/piclaw/actions/workflows/ansible-ci.yml/badge.svg)](https://github.com/kpeacocke/piclaw/actions/workflows/ansible-ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/)
[![Ansible 2.20+](https://img.shields.io/badge/ansible-2.20%2B-blue.svg)](https://ansible.com/)

Deploy a **privacy-preserving AI inference gateway** on Raspberry Pi 5 + AI HAT+ 2 using Ansible. Run large language models locally on edge hardware with hardware acceleration (Hailo NPU) and expose them via an **OpenAI-compatible API**.

## What You Get

- **OpenClaw Gateway** — OpenAI-compatible REST API for local LLM inference
  - Web UI (Canvas) for interactive chat
  - Streaming completions support
  - No cloud dependency, no API keys sent externally
- **Hailo NPU Acceleration** — Hardware-accelerated inference on AI HAT+ 2 (Hailo-10H)
- **Ollama Integration** — Local model management (pull, load, cache)
- **Flexible Profiles**
  - `local-safe`: Fully local inference (privacy-first)
  - `external-power`: Fallback to cloud providers (OpenAI, etc.)
- **Idempotent Ansible Playbooks** — Repeatable, validated deployments
- **CI/CD Ready** — Pre-commit hooks, linting, molecule testing, GitHub Actions

## Quick Start

### Prerequisites

- **Hardware**: Raspberry Pi 5 + AI HAT+ 2 (Hailo-10H)
- **OS**: Raspberry Pi OS Trixie 64-bit (fresh install recommended)
- **Control Host**: Ansible 2.20+ with Python 3.14+

### 1. Configure Target Host & Tailscale Auth Key

**Edit `inventories/prod/hosts.yml`** to point to your Pi:

```yaml
pi5-node:
  ansible_host: 192.168.1.50  # ← Update to your Pi's IP (or Tailscale IP after first deploy)
  ansible_user: pi
```

**Obtain a Tailscale auth key** (required for bootstrap):
1. Go to https://login.tailscale.com/admin/settings/keys
2. Click **Generate auth key**
3. ✅ Check "Reusable" (allows multiple devices)
4. Copy the key: `tskey-auth-<base64>`
5. Store it in AWX as a secret credential or encrypted inventory variable

### 2. Run Playbooks (in order)

```bash
# 1. Bootstrap: Tailscale, OS packages, firmware, Hailo runtime
ansible-playbook playbooks/bootstrap.yml -l pi5

# 2. Deploy: Ollama + OpenClaw gateway
ansible-playbook playbooks/openclaw.yml -l pi5

# 3. Verify: Functional tests (chat roundtrip, health checks)
ansible-playbook playbooks/verify.yml -l pi5
```

### 3. Use the Gateway

OpenClaw listens on `127.0.0.1:18789` and is accessible via **Tailscale mesh VPN** for secure, encrypted device-to-device access.

#### Access via Tailscale (Recommended)

1. **Join the Tailscale network**:
   - Install [Tailscale](https://tailscale.com/download) on your control machine
   - Sign in with your Tailscale account
   - Your Pi will auto-join during bootstrap with the auth key you provided

2. **Find the Pi's Tailscale IP**:
   ```bash
   tailscale list  # Shows all devices; look for your pi5 hostname
   # Example: pi5 (100.100.100.50) to authenticate; created Apr 20, 2026
   ```

3. **Access OpenClaw via Tailscale**:
   ```bash
   # Web UI (Canvas)
   open http://100.100.100.50:18789/__openclaw__/canvas/

   # CLI
   ssh pi@100.100.100.50 openclaw chat

   # OpenAI-compatible API
   curl http://100.100.100.50:18789/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "ollama/llama3.2:3b",
       "messages": [{"role": "user", "content": "Hello from Tailscale!"}]
     }'
   ```

#### Legacy SSH Port-Forward (if Tailscale unavailable)

```bash
ssh -L 18789:127.0.0.1:18789 pi@<pi5-ip>

# Then access at http://localhost:18789/...
```

## Deployment Modes

### Standalone (CLI)

```bash
# Copy repo to your control machine
git clone https://github.com/kpeacocke/piclaw.git
cd piclaw

# Set up local dev environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ansible-galaxy collection install -r collections/requirements.yml

# Run playbooks
ansible-playbook playbooks/bootstrap.yml -l pi5
ansible-playbook playbooks/openclaw.yml -l pi5
ansible-playbook playbooks/verify.yml -l pi5
```

### AWX (Orchestration)

Import job templates from `awx/job_templates.yml`. AWX manages:
- Inventory + host vars
- Survey-driven variable overrides
- Secrets injection
- Job history and audit logs
- Execution on execution nodes

See [AWX Setup](#awx-setup) for details.

## Configuration

### Core Variables

Repository defaults live in each role's `defaults/main.yml`. Override them in one of:

1. `group_vars/pi5.yml` — For all Pi 5s in the inventory
2. AWX inventory/group/host vars — Per-host overrides
3. Playbook `extra_vars` — Runtime via CLI or survey

### Key Options

**OpenClaw Profile** (`openclaw_profile`)
- `local-safe` (default) — All inference runs on Hailo NPU via Ollama
- `external-power` — Fallback to cloud API (e.g., OpenAI)

**Model Selection** (`hailo_model`)
- Default: `llama3.2:3b` (3B parameter, strongest installed Hailo-backed local model)
- Options: Any Ollama model compatible with Hailo's quantization constraints

**Sanitizer Proxy** (`use_sanitizer_proxy`)
- Enabled by default — Adds safety layer to Ollama responses
- Set to `false` to skip

**External Provider** (for `external-power`)
```yaml
openclaw_external_provider_name: custom
openclaw_external_provider_base_url: https://api.openai.com/v1
openclaw_external_provider_api: openai-completions
openclaw_external_provider_model: gpt-4-mini
openclaw_external_provider_api_key_env: OPENAI_API_KEY
```

**Tailscale Mesh VPN** (`tailscale_auth_key`)
- **Required** — Obtain a reusable auth key from https://login.tailscale.com/admin/settings/keys
  1. Go to **Settings > Keys**
  2. Click **Generate auth key**
  3. ✅ Check "Reusable" (allows multiple devices)
  4. Copy the key: `tskey-auth-<base64>`
- Provide it via an AWX custom credential, an encrypted AWX inventory/group variable, or an Ansible vault file
- Enables secure, encrypted mesh VPN access to all services
- Replaces LAN allowlists with Tailscale network boundary

**Additional Tailscale Options**
```yaml
tailscale_device_name: "pi5"  # Custom hostname on Tailscale network
tailscale_accept_dns: true    # Let Tailscale manage system DNS
tailscale_advertise_routes: false  # Advertise routes to other devices
tailscale_advertise_exit_node: false  # Don't route all traffic through Pi
```

## What Gets Installed & Validated

Each playbook enforces a known-good state:

### `bootstrap.yml`
- **Tailscale** — Mesh VPN agent (joins your Tailscale network via auth key)
- OS packages and security updates
- Firmware updates + reboot handling
- PCIe Gen 3.0 optimization
- Hailo runtime and driver installation
- Hardware probe (PCIe enumeration check)

### `openclaw.yml`
- Hailo Ollama integration (model pull and cache)
- OpenClaw installer and systemd service
- Provider configuration (local or external)
- Optional sanitizer proxy
- Port 18789 is available and responding

### `verify.yml`
- Smoke test: Chat roundtrip (request → response)
- Health checks: Gateway and Ollama health endpoints
- Doctor verification: System readiness report

## Repository Structure

```
.
├── playbooks/
│   ├── bootstrap.yml      # OS setup, firmware, Hailo runtime
│   ├── openclaw.yml       # Ollama, gateway, provider config
│   └── verify.yml         # Smoke tests and health checks
├── roles/
│   ├── base/              # OS packages, EEPROM, PCIe config
│   ├── hailo/             # Hailo runtime and driver
│   ├── hailo_ollama/      # Ollama + model integration
│   ├── openclaw/          # OpenClaw gateway + systemd
│   └── validate/          # Verification and smoke tests
├── inventories/
│   └── prod/hosts.yml     # Target Pi host and group vars
├── group_vars/
│   ├── pi5.yml            # Local overrides
│   └── pi5.vault.yml.example
├── awx/                   # Job template and survey specs
├── collections/
│   └── requirements.yml    # Ansible collection dependencies
├── molecule/
│   └── default/           # Role testing (syntax/lint focused)
├── tests/
│   └── test_molecule_default.py
└── .github/
    ├── workflows/         # CI/CD automation (lint, test, release)
    └── ISSUE_TEMPLATE/    # Bug and feature templates
```

## Development

### Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
ansible-galaxy collection install -r collections/requirements.yml
pre-commit install
```

### Quality Checks

```bash
# All checks in one go
pre-commit run --all-files

# Individual checks
ansible-lint                                         # Playbook lint
yamllint .                                          # YAML syntax
ansible-playbook --syntax-check playbooks/*.yml    # Ansible syntax
molecule test                                       # Role testing
pytest                                              # Python unit tests
```

All checks pass by default before commit (pre-commit hooks).

### Running on Hardware

Test code changes on a real Pi before submitting a PR:

```bash
# Get Pi's Tailscale IP: tailscale list | grep pi5
# Assuming Pi's Tailscale IP is 100.100.100.50

# SSH to the Pi via Tailscale and check status
ssh pi@100.100.100.50 openclaw status

# Re-run a single playbook from your control machine
ansible-playbook playbooks/openclaw.yml -l pi5 -v

# Check logs on the Pi
ssh pi@100.100.100.50 journalctl -u openclaw -n 50 -f
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branching, PRs, and release workflow.

## AWX Setup

### Quick Import

Job templates, surveys, and credential examples are defined in `awx/job_templates.yml`, `awx/surveys.yml`, and `awx/credentials.yml`. Create them in AWX via:

1. **API**: `awx-cli` or `curl` with the YAML spec
2. **UI**: Create manually, use the specs as reference
3. **Automation**: Third-party AWX provisioning tools

### Key Configuration

**Tailscale Secret Storage**

Do not keep the Tailscale auth key in a survey. Store it once in AWX and let the bootstrap job consume it automatically.

Recommended options:

1. **Custom AWX credential**
  - Create a credential type with one secret field: `tailscale_auth_key`
  - Paste the field schema into `Input configuration`
  - Paste the variable injection into `Injector configuration` or `Output configuration`, depending on your AWX version
  - Attach that credential to `piclaw-bootstrap`
  - Use `awx/credentials.yml` as the source-controlled reference

2. **Encrypted inventory/group variable**
  - Put `tailscale_auth_key` in the AWX inventory or group vars UI
  - Mark it as a secret if your AWX version supports secret inputs for that path

The bootstrap template no longer prompts for this value by default.

**Galaxy Credential Requirement**

Attach an Ansible Galaxy or Automation Hub credential to your AWX organization. Without it, collection sync skips and jobs fail with `couldn't resolve module/action 'community.docker...'`.

**Receptor Topology**

Ensure direct connection from AWX Receptor to execution nodes:

```
awx-task ↔ awx-receptor ↔ execution-node
```

Do **not** relay through a hop with a different Receptor version.

**Runtime Path**

AWX's `purge_old_stdout_files` task requires `/var/lib/awx/job_status/` in `awx-task`. Add to the entrypoint:

```bash
mkdir -p /var/lib/awx/job_status
```

### Execution Order

Run templates in this order:

1. `piclaw-bootstrap` — OS and runtime setup
2. `piclaw-openclaw` — Ollama + gateway (surveys: profile, model, provider)
3. `piclaw-verify` — Validation and smoke tests

See `awx/surveys.yml` for survey question specs and defaults.

## Security & Secrets

- **Never commit secrets** to git (passwords, API keys, hostnames)
- **Vault encryption** available: `ansible-vault encrypt group_vars/pi5.vault.yml`
- **AWX secrets**: Prefer credential plugins or encrypted inventory vars; avoid surveys for persistent secrets
- **API keys** (for external providers): Injected at runtime via environment variables, not in playbooks

For sensitive deployments:
- Manage inventory in a private repo
- Use AWX's credential store for API keys
- Rotate secrets regularly

## GitHub Automation

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ansible-ci` | PR, push | Lint, syntax check, secret scan |
| `scheduled-verify` | Weekly | Catch regressions early |
| `pr-labeler` | PR | Auto-label by changed paths |
| `label-sync` | Push to main | Sync issue labels from `.github/labels.yml` |
| `release-drafter` | PR merge | Draft semantic release notes |
| `publish-release` | Manual | Tag release and publish |
| `scorecard` | Weekly | OpenSSF security posture |

## Contributing

1. **Fork** the repository
2. **Create a branch** for your feature/fix
3. **Run quality checks** locally (`pre-commit run --all-files`)
4. **Test on hardware** if changes affect deployment
5. **Submit a PR** with a clear, conventional commit title (`feat:`, `fix:`, `chore:`, etc.)
6. **Request review** from maintainers

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed workflow and PR expectations.

## Support

- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/kpeacocke/piclaw/discussions)
- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/kpeacocke/piclaw/issues)
- **Security**: Report vulnerabilities via [GitHub Security Advisories](https://github.com/kpeacocke/piclaw/security/advisories/new) (private)

## License

Licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Raspberry Pi Foundation (hardware platform)
- Hailo (NPU hardware and runtime)
- Ollama (model management)
- OpenClaw (LLM inference gateway)
- Ansible (infrastructure automation)
