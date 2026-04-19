## Summary

What changed and why.

## Validation

- [ ] `pre-commit run --all-files`
- [ ] `ansible-playbook --syntax-check playbooks/bootstrap.yml`
- [ ] `ansible-playbook --syntax-check playbooks/openclaw.yml`
- [ ] `ansible-playbook --syntax-check playbooks/verify.yml`
- [ ] `molecule test`
- [ ] `pytest`

## Checklist

- [ ] No secrets committed
- [ ] Docs/vars updated if behavior changed
