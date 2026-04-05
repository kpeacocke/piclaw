# Pi 5 + AI HAT+ 2 OpenClaw Runbook (Ansible)

This repository enforces a known-good state for Raspberry Pi 5 + AI HAT+ 2 using Ansible.

## Assumptions

- Raspberry Pi 5
- Raspberry Pi OS Trixie 64-bit
- AI HAT+ 2 (Hailo-10H)
- Local inference and OpenClaw flavor

## Package Guardrail

- Use `hailo-h10-all` on AI HAT+ 2
- Do not mix with `hailo-all` on this hardware

## Repository Layout

- `inventories/prod/hosts.yml`
- `group_vars/pi5.yml`
- `roles/base`
- `roles/hailo`
- `roles/hailo_ollama`
- `roles/openclaw`
- `roles/validate`
- `playbooks/bootstrap.yml`
- `playbooks/openclaw.yml`
- `playbooks/verify.yml`

## Configure Variables

Edit `group_vars/pi5.yml`:

- `pi_user`
- `use_sanitizer_proxy`
- `claw_flavor`
- `hailo_model`
- `hailo_bind_host`
- `hailo_port`
- `proxy_port`
- `openclaw_provider_base_url`
- `openclaw_config_path` (if your install path differs)

Edit inventory host target in `inventories/prod/hosts.yml`.

## Execution Order

```bash
ansible-playbook playbooks/bootstrap.yml -l pi5
ansible-playbook playbooks/openclaw.yml -l pi5
ansible-playbook playbooks/verify.yml -l pi5
```

## Development Bootstrap

Install local development tooling and hooks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
ansible-galaxy collection install -r collections/requirements.yml
pre-commit install
```

Run quality gates locally:

```bash
pre-commit run --all-files
ansible-playbook --syntax-check playbooks/bootstrap.yml
ansible-playbook --syntax-check playbooks/openclaw.yml
ansible-playbook --syntax-check playbooks/verify.yml
```

See `CONTRIBUTING.md` for contribution workflow details.

## GitHub Automation Included

- CI workflow for lint + syntax checks:
	- `.github/workflows/ansible-ci.yml`
- Weekly scheduled syntax verification workflow:
	- `.github/workflows/scheduled-verify.yml`
- PR auto-labeling by changed paths:
	- `.github/workflows/pr-labeler.yml`
	- `.github/labeler.yml`
- Stale issue/PR lifecycle automation:
	- `.github/workflows/stale.yml`
- Release draft automation:
	- `.github/workflows/release-drafter.yml`
	- `.github/release-drafter.yml`
- Semantic PR title enforcement (Conventional Commits):
	- `.github/workflows/semantic-pr.yml`
- Manual publish of SemVer release from draft:
	- `.github/workflows/publish-release.yml`
- Dependabot for `pip` and GitHub Actions updates:
	- `.github/dependabot.yml`
- PR template and issue templates:
	- `.github/pull_request_template.md`
	- `.github/ISSUE_TEMPLATE/bug_report.yml`
	- `.github/ISSUE_TEMPLATE/feature_request.yml`
- CODEOWNERS:
	- `.github/CODEOWNERS`

## Governance Files

- License: Apache-2.0 in `LICENSE`
- Apache notice file in `NOTICE`
- Security disclosure guidance in `.github/SECURITY.md`
- Support guidance in `.github/SUPPORT.md`
- Issue template config in `.github/ISSUE_TEMPLATE/config.yml`
- Release note categories in `.github/release.yml`

## SemVer Release Flow

1. Use Conventional Commit PR titles (for example: `feat: add verify artifact output`, `fix: correct hailo probe check`).
2. `semantic-pr` workflow validates title format.
3. `release-drafter` auto-labels and computes next SemVer (`major`/`minor`/`patch`).
4. Run `publish-release` workflow when ready to publish the drafted release and tag.

## What Gets Enforced

- Base OS packages and upgrades
- EEPROM update + reboot handling
- Hailo PCIe detection
- Hailo runtime installation and checks
- Hailo Ollama availability and model pull
- OpenClaw installer execution and provider URL validation
- Optional sanitizer proxy checks
- Functional prompt roundtrip checks
