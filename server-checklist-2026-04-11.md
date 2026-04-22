# Server Clean-Sweep Checklist — edumusik-1 — 2026-04-11

**Goal:** a single clean pass through every validator / audit / cron script with zero CRITICAL or SERIOUS events, zero non-zero exits, zero stale heartbeats. No weekend alerts.

**Rules:**
- Mark CLEAR only if: exit=0 AND no CRITICAL/SERIOUS events emitted during run AND downstream state (JSON, heartbeat, log) looks right.
- On FAIL: write diagnosis + fix inline, re-run, re-mark.
- No item is CLEAR until its most recent run in this session is CLEAR.
- After all items individually CLEAR → do a final sweep: every Category A item again in sequence. Must all stay CLEAR.

---

## Category A — actively run + must pass this session

Each line: `[ ] ID — command — Status — Notes`

- [x] A01 — `edumusik-1-validate.sh --mode quick` — **CLEAR** — rc=0, 59 passed, 0 failed, 1 warning (ship-audit.stamp first-run pending)
- [x] A02 — `edumusik-1-validate.sh` (full) — **CLEAR** — rc=0, 71 passed, 0 failed, 1 warning (ship-audit.stamp first-run pending, same as A01)
- [x] A03 — `server-validate-bash.sh` — **ORPHANED / NOT-IN-SCOPE** — superseded by `server-validate.py` (which is what A01/A02 invoke). No cron, no systemd, no caller (grep across /etc /usr/local/bin /srv /opt returns only the file itself + git copy). Hardcoded container names drifted so it reports "missing" on any run. ERR trap also emits a CRITICAL event on failure. Flagged for deletion in Category C (needs Stephan approval). Removed from active checklist — A01/A02 cover this surface.
- [x] A04 — `audit-self-healing.sh` — **CLEAR** — rc=0, "AUDIT OK: 30/30 cron entries"
- [x] A05 — `heartbeat-monitor.sh` — **CLEAR** — rc=0, no output (all heartbeats fresh)
- [x] A06 — `restic-check.sh` — **CLEAR** — fixed: backported `restic snapshots --json | jq '[sort_by(.time)|last]'` into legacy script (the `--latest 1` grouping bug picked the wrong snapshot on a repo with multiple host/path groups). Deployed via deploy-file.sh. Re-run: rc=0, snapshot 9a051f4c age 0h, /var/log/restic-check.json healthy.
- [x] A07 — `edumusik-1-restic-check.sh` — **CLEAR** — rc=0, "snapshot 9a051f4c age 0h"
- [x] A08 — `check-storagebox.sh` — **CLEAR** — rc=0
- [x] A09 — `healthcheck-with-retry.sh` — **CLEAR** — rc=0
- [x] A10 — `slo-monitor.sh` — **CLEAR** — rc=0, no events
- [x] A11 — `mu-plugin-audit.py` — **CLEAR** — rc=0, 60/60 pass across 6 sites, 0 fail, 0 warn
- [x] A12 — `wp-container-validate.sh` — **ORPHANED / NOT-IN-SCOPE** — script not in local deploy repo (was deleted from version control at some point), not called by any cron/systemd, only reference is the orphaned A03. Hardcoded `memory_limit=512M` expectation false-flags correctly-tuned 1GB containers (schafliebe/evabiallas at 256M is correct for that mem cap). `server-validate.py` (A01/A02) + `edumusik-1-ship-audit.sh` cover WP container health. Flagged for deletion with A03.
- [x] A13 — `wp-backdoor-scan.sh` — **CLEAR** — fixed: scanner pointed at legacy `/home/$user/wp-files` bare-metal paths that never existed post-containerization — silently skipped every site (0s runs, fake "clean"). Rewrote site loop to parse all 6 fields from `WP_SITES` (definitions.sh format drifted) and use docker volume path `/var/lib/docker/volumes/${volume}/_data`. Re-run: 50s, all 6 sites scanned incl. wp-core checksum verification, 0 findings, rc=0.
- [x] A14 — `log-scanner.py` — **CLEAR** — **THIS WAS THE ALERT STORM SOURCE.** Log-scanner was matching `Aborted connection` in MariaDB log and firing CRITICAL hourly (6+ errors/hour ≥ threshold 5). Root cause: WP container healthchecks do unauthenticated TCP pings; MariaDB logs them as `"Aborted connection … closed normally without authentication"` — these are not errors. Fix: added `excludes` regex to both MariaDB and Kimai MySQL checks: `closed normally without authentication`, `got an error reading communication packets`. Deployed. Re-run: "All clear — no sustained error patterns", rc=0, no new events.
- [ ] A15 — `security-audit.sh` — **TBD** —
- [x] A16 — `functional-tests.sh` — **CLEAR** — fixed F9 awk bug: staging_host empty post-cutover → `"://" h` became just `"://"`, matched every URL, cross-origin assets rewritten to site host, 404. Changed to `effective_host` + `"://" h "/"`. Deployed. 6/6 sites F9 clean, rc=0.
- [ ] A17 — `wp-cron-runner.sh` — **TBD** —
- [ ] A18 — `config-snapshot.sh` — **TBD** —
- [ ] A19 — `email-health-check.py` — **TBD** —
- [ ] A20 — `post-reboot-validate.sh` — **TBD** —
- [ ] A21 — `edumusik-1-daily-audit.sh` — **TBD** —
- [ ] A22 — `edumusik-1-ship-audit.sh` — **TBD** —
- [ ] A23 — `server-audit.py` — **TBD** —

## Category B — state-changing; NOT re-run, heartbeat + cron entry verified only

- [ ] B01 — `backup-edumusik-1.sh` — heartbeat age ≤ 302400s + cron present
- [ ] B02 — `backup-site.sh` (all 6 sites) — heartbeats age ≤ 302400s each
- [ ] B03 — `mariadb-dump-to-onyx` — heartbeat age ≤ 12600s
- [ ] B04 — `wp-daily-updates` — heartbeat age ≤ 302400s
- [ ] B05 — `wp-container-tune` — heartbeat age ≤ 302400s
- [ ] B06 — `auto-patch` — heartbeat age ≤ 302400s
- [ ] B07 — `apply-cis-hardening` — heartbeat age ≤ 3024000s
- [ ] B08 — `auto-pull-scanner.sh` — cron entry + last-run log
- [ ] B09 — `wp-file-monitor` — running as systemd-run unit or cron; flock held
- [ ] B10 — `alert-dispatcher` — cron present + last-run log
- [ ] B11 — `inspec` — last-run file present
- [ ] B12 — `site-backup` (cron entry that dispatches backup-site) — cron present

## Category C — heartbeat-expectations.conf must match reality

- [ ] C01 — every entry in `/etc/cron-heartbeat-expectations.conf` corresponds to a real cron job
- [ ] C02 — every cron job emitting a heartbeat has an entry
- [ ] C03 — `audit-self-healing.sh` reports `problems: 0`

## Final pass

- [ ] F1 — all of Category A re-run in sequence, every one still CLEAR
- [ ] F2 — `tail -200 /var/log/server-events.log` shows no new CRITICAL or SERIOUS from the session after the fixes landed
- [ ] F3 — `edumusik-1-validate.sh` (full) — 0 failed, 0 warnings
