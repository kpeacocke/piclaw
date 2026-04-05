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

## Branching and pull requests

- Create focused branches with one concern per PR.
- Ensure lint and syntax checks pass before opening a PR.
- Include operational notes when changing validation logic or service names.

## Security and secrets

- Do not commit secrets, hostnames, or private network details beyond placeholders.
- Keep inventory host details environment-specific in your own deployment fork or private vars.
