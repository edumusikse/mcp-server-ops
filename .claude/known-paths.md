# Known Paths Reference

Check here BEFORE running `find` or `grep -r`. If the path is listed, use it directly.
After discovering new paths via find, add them here before continuing.

## ops-agent project (local)

### MCP server (`server/`)
- Entry point: `server/server.py`
- Transport + fleet config: `server/transport.py`
- Fleet tools: `server/fleet.py`
- WordPress tools: `server/wp.py`
- Compose tools: `server/compose.py`
- File I/O tools: `server/files.py`
- Runbook tools: `server/runbook.py`
- Cloud tools: `server/cloud.py`
- Deploy tools: `server/deploy.py`
- Guards: `server/guards.py`

### Tests (`tests/`)
- Tool count / import check: `tests/test_server_imports.py`
- Thrash guard: `tests/test_thrash_guard.py`
- Payload guard: `tests/test_payload_guard.py`
- Runbook hygiene: `tests/test_runbook_hygiene.py`
- Runbook guard: `tests/test_runbook_guard.py`
- Budget guard: `tests/test_budget_guard.py`
- Workspace health: `tests/test_workspace_health.py`
- Runbook compliance: `tests/runbook_compliance.py`
- Live ops parity: `tests/live_ops_parity.py`
- Audit script: `tests/audit.sh`

### Hooks + settings
- All hooks: `.claude/hooks/`
- Project settings: `.claude/settings.json`
- Known paths (this file): `.claude/known-paths.md`

### server-config sub-repo (`server-config/`)
- WP panel Flask app: `server-config/wp-panel/app.py`
- Security audit dashboard (HTML): `server-config/security-audit/dashboard.html`
- Security audit backend (Flask): `server-config/security-audit/dashboard.py`
- Security audit report generator: `server-config/security-audit/security-audit-report.py`
- Security audit suppressions: `server-config/security-audit/suppressions.json`
- Security audit shell script: `server-config/scripts/security-audit.sh`
- Validator runner: `server-config/scripts/validator/run.py`
- WP daily updates: `server-config/scripts/wp-daily-updates.py`
- Deploy script: `server-config/_deploy_server.py`

### wp-edumusik-net sub-repo (`wp-edumusik-net/`)
- Admin menu mu-plugin (registers all WP Admin subpages): `wp-edumusik-net/mu-plugins/server-admin-links.php`
- All mu-plugins dir: `wp-edumusik-net/mu-plugins/`
- Edubuild loader: `wp-edumusik-net/mu-plugins/edubuild-loader.php`

## On-server paths

Readable via `read_file` (allowed prefixes: /var/log/, /srv/, /opt/, /usr/local/bin/, /home/stephan/.ops-mcp/, /var/lib/ai-agent/).
Scripts at /usr/local/bin/ are NOT readable via read_file — read the local server-config/ copy instead.

### main (192.168.50.3)
- WP panel service: `/opt/wp-panel/app.py`
- Security audit service: `/opt/security-audit/` (dashboard.py, dashboard.html)
- Security audit logs: `/var/log/security-audit/YYYY-MM-DD.json`
- Security audit latest AIDE: `/var/log/security-audit/aide-latest.json`
- Security audit latest InSpec: `/var/log/security-audit/inspec-latest.json`
- Operational event log: `/var/log/server-events.log`
- Server audit JSON: `/var/log/server-audit.json`
- Backup log: `/var/log/backup.log`
- MariaDB dump log: `/var/log/mariadb-dump.log`

### onyx (control server)
- MCP server entry: `/opt/ops-mcp/server.py`
- Fleet config: `/opt/ops-mcp/hosts.yaml`
- Secrets: `/opt/ops-mcp/.env`
- Docs dir: `/opt/ops-mcp/docs/`
- State DB: `~/.ops-mcp/state.db`
- MCP process log: `~/.ops-mcp/ops-mcp.log`
