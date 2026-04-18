(function () {
    const vscode = acquireVsCodeApi();
    const modelSelect = document.getElementById('model-select');
    const messages    = document.getElementById('messages');
    const input       = document.getElementById('input');
    const sendBtn     = document.getElementById('send-btn');
    const statusDot   = document.getElementById('status-dot');

    let currentAssistantEl = null;
    let currentBodyEl = null;

    // ── Send ──────────────────────────────────────────────────────────────────

    function send() {
        const text = input.value.trim();
        if (!text) return;
        appendMsg('user', text);
        vscode.postMessage({ type: 'send', model: modelSelect.value, text });
        input.value = '';
        setbusy(true);
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send();
    });

    // ── Messages ──────────────────────────────────────────────────────────────

    function appendMsg(role, text) {
        const wrap  = document.createElement('div');
        wrap.className = `msg ${role}`;
        const label = document.createElement('div');
        label.className = 'msg-label';
        label.textContent = role === 'user' ? 'You' : 'Assistant';
        const body  = document.createElement('div');
        body.className = 'msg-body';
        body.textContent = text;
        wrap.appendChild(label);
        wrap.appendChild(body);
        messages.appendChild(wrap);
        scrollBottom();
        return { wrap, body };
    }

    function scrollBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    // ── Extension → webview messages ──────────────────────────────────────────

    window.addEventListener('message', e => {
        const msg = e.data;
        switch (msg.type) {

            case 'models':
                modelSelect.innerHTML = '';
                for (const m of msg.models) {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.textContent = m.label;
                    modelSelect.appendChild(opt);
                }
                break;

            case 'status':
                statusDot.className = 'dot ' + (msg.connected ? 'connected' : 'error');
                statusDot.title = msg.connected
                    ? `MCP connected · ${msg.toolCount} tools`
                    : `MCP error: ${msg.error}`;
                break;

            case 'startAssistant': {
                const { wrap, body } = appendMsg('assistant', '');
                body.classList.add('cursor');
                currentAssistantEl = wrap;
                currentBodyEl = body;
                break;
            }

            case 'chunk':
                if (currentBodyEl) {
                    currentBodyEl.textContent += msg.text;
                    scrollBottom();
                }
                break;

            case 'toolStart': {
                const chip = document.createElement('div');
                chip.className = 'tool-chip running';
                chip.id = 'tool-' + msg.name;
                chip.textContent = msg.name;
                currentAssistantEl?.appendChild(chip);
                scrollBottom();
                break;
            }

            case 'toolEnd': {
                const chip = document.getElementById('tool-' + msg.name);
                if (chip) { chip.className = 'tool-chip done'; }
                break;
            }

            case 'error': {
                const err = document.createElement('div');
                err.className = 'error-msg';
                err.textContent = '⚠ ' + msg.message;
                messages.appendChild(err);
                scrollBottom();
                break;
            }

            case 'done':
                if (currentBodyEl) currentBodyEl.classList.remove('cursor');
                currentAssistantEl = null;
                currentBodyEl = null;
                setbusy(false);
                break;

            case 'cleared':
                messages.innerHTML = '';
                break;
        }
    });

    function setbusy(busy) {
        sendBtn.disabled = busy;
        input.disabled   = busy;
    }

    // Signal ready
    vscode.postMessage({ type: 'ready' });
}());
