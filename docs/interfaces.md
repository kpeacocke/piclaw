# Interfaces

## Ansible deployment

Run the playbooks from the repository root with `ansible-playbook` and an
inventory containing the `pi5` group. Pass the inventory explicitly, for example
`ansible-playbook -i inventories/prod/hosts.yml playbooks/bootstrap.yml -l pi5`.
`ansible.cfg` does not set a default inventory. `bootstrap.yml` installs the platform, `openclaw.yml` deploys
services, and `verify.yml` checks the resulting deployment.

Inputs are inventory host addresses and SSH credentials, role defaults,
`group_vars/pi5.yml`, encrypted vault variables, and optional `--extra-vars`.
Keep credentials in Ansible Vault or AWX credentials. Each role's
`defaults/main.yml` is the reference for supported configuration names and
defaults. AWX survey and credential schemas are in `awx/`.

Output is Ansible's task recap and changed/failed task results. A nonzero exit
status indicates failure; inspect the failing task before retrying. Provisioning
changes packages, files and systemd services on the target and can reboot it.
The playbooks require Linux and the documented Raspberry Pi hardware; syntax
checks and unit tests do not establish hardware compatibility.

## Sanitizer proxy

`hailo-sanitize-proxy.py` listens on port 8081 and forwards inference requests to
`http://127.0.0.1:8000`. `HAILO_PROXY_LISTEN_HOST` sets the bind address.
`HAILO_MODEL` sets the default model identifier. The constants at the top of the
script document environment configuration for origins, hosts, tracing and
timeouts.

Clients submit JSON to `/v1/chat/completions`, including a model and messages
with roles and text content. Unsupported request fields are stripped, prompts
are reduced for the upstream context, and upstream streaming is disabled.
Responses use OpenAI-compatible JSON; requests with `stream: true` receive
server-sent events synthesized from the upstream response. `/v1/models`
provides model discovery and `/api/show` provides compatibility metadata.
Upstream HTTP failures are returned as error responses. This adapter does not
promise compatibility with every OpenAI API feature.

HTTP on loopback is intended for local service communication. A Host header or
CORS policy is not authentication. Restrict access with the host firewall and
Tailscale access controls; do not expose the inference ports to the public
Internet. Use authenticated encrypted transport for remote access, or the SSH
port-forward described in the README.
