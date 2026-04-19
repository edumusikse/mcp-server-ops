(function () {
    const vscode = acquireVsCodeApi();
    const bodyEl    = document.getElementById('fleet-body');
    const updatedEl = document.getElementById('fleet-updated');
    const statusDot = document.getElementById('fleet-status-dot');
    const refreshBtn = document.getElementById('fleet-refresh');
    const probesBtn  = document.getElementById('fleet-run-probes');
    const toastEl    = document.getElementById('fleet-toast');

    refreshBtn.addEventListener('click', () => vscode.postMessage({ type: 'refresh' }));
    probesBtn.addEventListener('click',  () => vscode.postMessage({ type: 'runProbes' }));

    let pendingRestarts = new Set();

    // ── Formatting helpers ────────────────────────────────────────────────────

    function fmtAge(status) {
        // status is like "Up 3 days (healthy)" — extract the duration
        const m = /Up ([^(]+)/.exec(status || '');
        return m ? m[1].trim() : (status || '');
    }

    function isHealthy(status) {
        if (!status) return false;
        if (/\(unhealthy\)/i.test(status)) return false;
        return /^Up /.test(status);
    }

    function statusClass(probeStatus) {
        switch (probeStatus) {
            case 'ok':    return 'probe-ok';
            case 'warn':  return 'probe-warn';
            case 'fail':  return 'probe-fail';
            case 'error': return 'probe-error';
            case 'skip':  return 'probe-skip';
            default:      return 'probe-unknown';
        }
    }

    function fmtTimestamp(ts) {
        const d = new Date(ts);
        return d.toLocaleTimeString('en-GB', { hour12: false });
    }

    function toast(msg, isError) {
        toastEl.textContent = msg;
        toastEl.className = 'fleet-toast' + (isError ? ' error' : '');
        setTimeout(() => toastEl.classList.add('hidden'), 4000);
    }

    // ── Render ────────────────────────────────────────────────────────────────

    // Restart-allowlist: UI-side mirror of server-side gate. Server enforces,
    // but greying out non-allowlisted containers keeps the UI honest.
    // This must match /opt/ops-mcp/hosts.yaml restart_allowlist.
    const RESTART_ALLOW = {
        onyx: new Set(['beszel-agent']),
        main: new Set([
            'beszel-agent',
            'ksm-wp', 'evabiallas-wp', 'schafliebe-wp', 'frid-wp',
            'edumusik-com-wp', 'edumusik-net-wp',
        ]),
    };

    function renderHost(hostName, hostData, healthByHost) {
        const health = healthByHost?.[hostName];
        const worst = health?.worst || null;
        const worstClass = worst ? statusClass(worst) : '';

        const containers = (hostData.containers || []).slice().sort((a, b) => {
            const aH = isHealthy(a.status);
            const bH = isHealthy(b.status);
            if (aH !== bH) return aH ? 1 : -1;  // unhealthy first
            return a.name.localeCompare(b.name);
        });

        const allowSet = RESTART_ALLOW[hostName] || new Set();

        const containerRows = containers.map(c => {
            const healthy = isHealthy(c.status);
            const statusDot = `<span class="cont-dot ${healthy ? 'ok' : 'bad'}"></span>`;
            const age = fmtAge(c.status);
            const canRestart = allowSet.has(c.name);
            const isPending = pendingRestarts.has(`${hostName}:${c.name}`);
            const btn = canRestart
                ? `<button class="cont-restart" data-host="${hostName}" data-container="${c.name}" ${isPending ? 'disabled' : ''}>${isPending ? '…' : '↻'}</button>`
                : `<button class="cont-restart disabled" title="Not in restart allowlist" disabled>·</button>`;
            return `
                <div class="cont-row">
                    ${statusDot}
                    <span class="cont-name">${c.name}</span>
                    <span class="cont-age">${age}</span>
                    ${btn}
                </div>`;
        }).join('');

        const disk = hostData.disk_pct;
        const ram = hostData.ram;
        const uptime = hostData.uptime || '';

        const failingProbes = (health?.failing || []).map(f =>
            `<div class="probe-line ${statusClass(f.status)}">
               <span class="probe-name">${f.probe}</span>
               ${f.container ? `<span class="probe-cont">${f.container}</span>` : ''}
               ${f.target ? `<span class="probe-target">${f.target}</span>` : ''}
             </div>`
        ).join('');

        const counts = health?.counts || {};
        const countBits = Object.entries(counts).map(
            ([k, v]) => `<span class="count-pill ${statusClass(k)}">${k}:${v}</span>`
        ).join('');

        return `
          <div class="host-card">
            <div class="host-head">
              <span class="host-name">${hostName}</span>
              <span class="host-meta">disk ${disk}% · ram ${ram?.pct ?? '?'}% · ${uptime}</span>
              ${worst ? `<span class="host-worst ${worstClass}">${worst}</span>` : ''}
            </div>
            ${countBits ? `<div class="probe-counts">${countBits}</div>` : ''}
            ${failingProbes ? `<div class="probe-failing">${failingProbes}</div>` : ''}
            <div class="cont-list">${containerRows}</div>
          </div>`;
    }

    function render(fleet) {
        const hosts = fleet.fleet || {};
        const health = fleet.health || {};
        const html = Object.keys(hosts).sort().map(h => renderHost(h, hosts[h], health)).join('');
        bodyEl.innerHTML = html || '<div class="fleet-empty">No hosts returned.</div>';

        // Wire up restart buttons
        bodyEl.querySelectorAll('.cont-restart:not(.disabled)').forEach(btn => {
            btn.addEventListener('click', () => {
                const host = btn.dataset.host;
                const container = btn.dataset.container;
                if (!confirm(`Restart ${container} on ${host}?`)) return;
                pendingRestarts.add(`${host}:${container}`);
                btn.disabled = true;
                btn.textContent = '…';
                vscode.postMessage({ type: 'restartContainer', host, container });
            });
        });
    }

    // ── Messages from extension ───────────────────────────────────────────────

    window.addEventListener('message', e => {
        const msg = e.data;
        switch (msg.type) {
            case 'status':
                statusDot.className = 'dot ' + (msg.connected ? 'connected' : 'error');
                statusDot.title = msg.connected ? 'MCP connected' : `MCP error: ${msg.error || ''}`;
                break;
            case 'fleet':
                render(msg.data);
                updatedEl.textContent = `updated ${fmtTimestamp(msg.ts)}`;
                break;
            case 'probesRunning':
                probesBtn.disabled = true;
                probesBtn.textContent = 'running…';
                break;
            case 'probesDone':
                probesBtn.disabled = false;
                probesBtn.textContent = '▶ probes';
                if (msg.error) toast(msg.error, true);
                else toast(`Probes done — worst: ${msg.data?.summary?.worst_status || '?'}`, false);
                break;
            case 'restartRunning':
                // UI already updated optimistically
                break;
            case 'restartDone':
                pendingRestarts.delete(`${msg.host}:${msg.container}`);
                if (msg.result?.ok) {
                    toast(`${msg.container}: restarted`, false);
                } else {
                    toast(`${msg.container}: ${msg.result?.error || 'failed'}`, true);
                }
                break;
        }
    });

    // Signal ready
    vscode.postMessage({ type: 'ready' });
}());
