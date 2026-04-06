# Contributing

## Local development setup

1. Create and install dev tooling:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements-dev.txt
   ansible-galaxy collection install -r collections/requirements.yml
   ```

2. Install git hooks:

   ```bash
   pre-commit install
   ```

3. Run quality gates:

   ```bash
   pre-commit run --all-files
   ansible-playbook --syntax-check playbooks/bootstrap.yml
   ansible-playbook --syntax-check playbooks/openclaw.yml
   ansible-playbook --syntax-check playbooks/verify.yml
   ```

## Updating the dependency lockfile

CI installs from `requirements-dev.lock` (hash-pinned). If you change `requirements-dev.txt`, regenerate the lockfile:

```bash
pip-compile --generate-hashes --allow-unsafe --output-file=requirements-dev.lock requirements-dev.txt
```

Commit both files together in the same PR.

## Branching and pull requests

- Create focused branches with one concern per PR.
- Ensure lint and syntax checks pass before opening a PR.
- Include operational notes when changing validation logic or service names.

## Security and secrets

- Do not commit secrets, hostnames, or private network details beyond placeholders.
- Keep inventory host details environment-specific in your own deployment fork or private vars.
- Pin `openclaw_installer_version` in `group_vars/pi5.yml` to a specific commit SHA before running against hardware.
