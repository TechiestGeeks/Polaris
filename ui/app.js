// ============ STATE ============
let currentUser = null;
let isBusy = false;
let conversationHistory = []; // [{question, answer, decision}]

// ============ INIT ============
document.addEventListener("DOMContentLoaded", async () => {
    const saved = localStorage.getItem('polaris_session');
    if (saved) {
        const cached = JSON.parse(saved);
        // Always re-fetch live data so admin changes (upgrades/downgrades) are reflected immediately
        try {
            const res = await fetch('/api/employees', { headers: { 'bypass-tunnel-reminder': 'true' } });
            const employees = await res.json();
            const fresh = employees.find(e => e.employee_id === cached.employee_id);
            if (fresh) {
                currentUser = { ...cached, ...fresh };
                localStorage.setItem('polaris_session', JSON.stringify(currentUser));
            } else {
                // Employee was deleted by admin — force logout
                localStorage.removeItem('polaris_session');
                showScreen('loginScreen');
                return;
            }
        } catch {
            // Offline fallback: use cached data
            currentUser = cached;
        }
        showScreen('homeScreen');
        populateUserUI();
    } else {
        showScreen('loginScreen');
    }

    // Enter key for login
    document.getElementById('loginPassword').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') login();
    });
    document.getElementById('loginUsername').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') document.getElementById('loginPassword').focus();
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.user-pill')) {
            document.querySelectorAll('.user-dropdown').forEach(d => d.classList.remove('open'));
        }
    });
});

// ============ SCREEN MANAGEMENT ============
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    window.scrollTo(0, 0);
}

function goHome() {
    showScreen('homeScreen');
    document.getElementById('homeSearchInput').value = '';
}

// ============ USER UI ============
function populateUserUI() {
    if (!currentUser) return;
    const initials = currentUser.name.split(' ').map(n => n[0]).join('').slice(0, 2);
    const info = `${currentUser.name} · ${currentUser.role}`;

    document.getElementById('headerAvatar').textContent = initials;
    document.getElementById('headerName').textContent = `Logged in as ${currentUser.name.split(' ')[0]}`;
    document.getElementById('ddProfile').textContent = info;

    document.getElementById('chatHeaderAvatar').textContent = initials;
    document.getElementById('chatHeaderName').textContent = `Logged in as ${currentUser.name.split(' ')[0]}`;
    document.getElementById('chatDdProfile').textContent = info;
    
    document.getElementById('msgHeaderAvatar').textContent = initials;
    document.getElementById('msgHeaderName').textContent = `Logged in as ${currentUser.name.split(' ')[0]}`;
    document.getElementById('msgDdProfile').textContent = info;
    
    // Initial fetch of messages
    loadMessages();
}

function toggleDropdown() {
    document.querySelectorAll('.user-dropdown').forEach(d => {
        const isActive = d.classList.contains('open');
        d.classList.toggle('open', !isActive);
    });
}

// ============ AUTH ============
async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    const btn = document.getElementById('loginBtn');

    if (!username || !password) {
        showError(errorDiv, 'Please enter your name and password.');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="login-spinner"></span>Signing in…';
    errorDiv.style.display = 'none';

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'bypass-tunnel-reminder': 'true' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');

        currentUser = data;
        localStorage.setItem('polaris_session', JSON.stringify(currentUser));
        populateUserUI();
        showScreen('homeScreen');

    } catch (e) {
        showError(errorDiv, e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Log in';
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('polaris_session');
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('chatBody').innerHTML = '';
    showScreen('loginScreen');
}

function showError(el, msg) {
    el.textContent = msg;
    el.style.display = 'block';
}

// ============ HOME ============
async function loadMessages() {
    if (!currentUser) return;
    try {
        const res = await fetch(`/api/messages/${currentUser.employee_id}`, { headers: { 'bypass-tunnel-reminder': 'true' } });
        const msgs = await res.json();
        
        // Update badges
        const pendingCount = msgs.filter(m => m.status === 'Pending').length;
        const b1 = document.getElementById('homeMsgBadge');
        const b2 = document.getElementById('chatMsgBadge');
        if (pendingCount > 0) {
            b1.textContent = pendingCount; b1.style.display = 'inline-block';
            b2.textContent = pendingCount; b2.style.display = 'inline-block';
        } else {
            b1.style.display = 'none'; b2.style.display = 'none';
        }
        
        // Render
        const list = document.getElementById('messagesList');
        if (msgs.length === 0) {
            list.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-s);">No escalations found.</div>`;
            return;
        }
        
        list.innerHTML = msgs.reverse().map(m => `
            <div class="answer-card" style="margin-bottom:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <div style="font-size:12px;font-family:monospace;font-weight:700;color:var(--text-s);">${m.id} &bull; ${new Date(m.timestamp).toLocaleDateString()}</div>
                    <span class="badge ${m.status === 'Pending' ? 'badge-review' : 'badge-active'}">${m.status}</span>
                </div>
                <div style="font-size:16px;font-weight:700;margin-bottom:16px;color:var(--navy);border:2px solid var(--navy);padding:12px;line-height:1.5;background:var(--yellow);box-shadow:4px 4px 0px 0px var(--navy);word-wrap:break-word;">"${escHtml(m.question)}"</div>
                ${m.admin_response ? `
                <div style="background:var(--bg-app);padding:12px;border-left:4px solid var(--accent);border-radius:4px;">
                    <div style="font-size:11px;text-transform:uppercase;font-weight:800;color:var(--accent);margin-bottom:4px;letter-spacing:0.05em;">Admin Resolution</div>
                    <div style="font-size:14px;color:var(--text-p);">${escHtml(m.admin_response)}</div>
                </div>
                ` : `<div style="font-size:13px;color:var(--text-s);font-style:italic;">Waiting for admin review...</div>`}
            </div>
        `).join('');
    } catch(e) { console.error("Failed to load messages", e); }
}

function showMessages() {
    loadMessages();
    showScreen('messagesScreen');
}

function fillQuestion(text) {
    document.getElementById('homeSearchInput').value = text;
    submitHomeSearch();
}

function handleHomeKey(e) {
    if (e.key === 'Enter') { e.preventDefault(); submitHomeSearch(); }
}

function submitHomeSearch() {
    const question = document.getElementById('homeSearchInput').value.trim();
    if (!question || isBusy) return;
    document.getElementById('chatBody').innerHTML = '';
    showScreen('chatScreen');
    setTimeout(() => sendQuestion(question), 50);
}

// ============ CHAT ============
function handleChatKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitChat(); }
}

function submitChat() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    if (!question || isBusy) return;
    input.value = '';
    autoResize(input);
    sendQuestion(question);
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

// ============ SEND QUESTION ============
// Memory-type question patterns answered directly from history
const MEMORY_PATTERNS = [
    /what (was|were|is) my (last|previous|prior) (question|message|query)/i,
    /what did i (ask|say) (last|before|previously|earlier)/i,
    /repeat my (last|previous) (question|message|query)/i,
    /what have i asked/i,
];

function isMemoryQuestion(q) {
    return MEMORY_PATTERNS.some(p => p.test(q));
}

function answerFromMemory(question) {
    if (conversationHistory.length === 0) {
        return { decision: 'ANSWER', answer: 'You haven\'t asked any questions yet in this session.' };
    }
    const last = conversationHistory[conversationHistory.length - 1];
    return {
        decision: 'ANSWER',
        answer: `Your last question was: **"${last.question}"**`,
        thinking_context: null,
        applicable_policies: []
    };
}

async function sendQuestion(question) {
    if (isBusy) return;
    isBusy = true;

    const body = document.getElementById('chatBody');
    document.getElementById('chatSendBtn').disabled = true;

    // Show question bubble
    appendQuestion(body, question);

    // Answer memory questions locally without hitting the backend
    if (isMemoryQuestion(question)) {
        const memData = answerFromMemory(question);
        appendAnswer(body, question, memData);
        isBusy = false;
        document.getElementById('chatSendBtn').disabled = false;
        body.scrollTop = body.scrollHeight;
        return;
    }

    // Show thinking indicator
    const thinkingEl = appendThinking(body);
    body.scrollTop = body.scrollHeight;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

        const res = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'bypass-tunnel-reminder': 'true' },
            body: JSON.stringify({ question, employee_id: currentUser.employee_id, history: conversationHistory }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const data = await res.json();

        thinkingEl.remove();

        if (!res.ok) throw new Error(data.detail || 'Server error');

        // Store in conversation history
        conversationHistory.push({ question, answer: data.answer, decision: data.decision });

        appendAnswer(body, question, data);

    } catch (e) {
        thinkingEl.remove();
        appendError(body, e.message);
    } finally {
        isBusy = false;
        document.getElementById('chatSendBtn').disabled = false;
        body.scrollTop = body.scrollHeight;
    }
}

// ============ DOM BUILDERS ============
function appendQuestion(body, text) {
    const row = document.createElement('div');
    row.className = 'message-row';
    row.innerHTML = `<div class="question-bubble">${escHtml(text)}</div>`;
    body.appendChild(row);
}

function appendThinking(body) {
    const el = document.createElement('div');
    el.className = 'thinking-indicator';
    el.innerHTML = `
        <div class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
        <span class="thinking-label">POLARIS is thinking…</span>
    `;
    body.appendChild(el);
    return el;
}

function appendAnswer(body, question, data) {
    const row = document.createElement('div');
    row.className = 'message-row';

    const decision = data.decision || 'N/A';
    let badgeClass = '';
    if (decision === 'DENY' || decision === 'MISSING_CONTEXT' || decision === 'NO_APPLICABLE_POLICY') badgeClass = 'deny';
    else if (decision === 'CONFLICT') badgeClass = 'conflict';
    else if (decision === 'ESCALATED') badgeClass = 'escalated';
    else if (decision === 'N/A' || decision === 'ANSWER') badgeClass = 'general';

    // Format answer text (preserve markdown bold)
    const answerHtml = formatAnswer(data.answer || '');

    const thinkingId = 'th-' + Date.now();
    const panelId = 'tp-' + Date.now();

    row.innerHTML = `
        <div class="answer-card">
            <div class="answer-badge ${badgeClass}">${decision === 'N/A' ? 'ANSWER' : decision}</div>
            <div class="answer-text">${answerHtml}</div>
            <div class="answer-actions">
                <button class="btn-ghost" onclick="askFollowUp(this)">Ask a follow-up</button>
                ${data.applicable_policies && data.applicable_policies.length ? `<button class="btn-ghost" onclick="showPolicyRef(this, '${encodePolicies(data.applicable_policies)}')">Policy reference</button>` : ''}
            </div>
            ${data.thinking_context ? `
                <button class="thinking-toggle" id="${thinkingId}" onclick="toggleThinking('${thinkingId}', '${panelId}')">
                    <span>Engine reasoning</span>
                    <span class="chevron">▾</span>
                </button>
                <div class="thinking-panel" id="${panelId}">${escHtml(data.thinking_context)}</div>
            ` : ''}
            <div class="audit-id">Audit: ${data.request_id}</div>
        </div>
    `;
    body.appendChild(row);
}

function appendError(body, msg) {
    const row = document.createElement('div');
    row.className = 'message-row';
    row.innerHTML = `
        <div class="answer-card">
            <div class="answer-badge deny">ERROR</div>
            <div class="answer-text" style="color: var(--red)">${escHtml(msg)}</div>
        </div>
    `;
    body.appendChild(row);
}

// ============ INTERACTIONS ============
function toggleThinking(btnId, panelId) {
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    const isOpen = panel.style.display === 'block';
    panel.style.display = isOpen ? 'none' : 'block';
    btn.classList.toggle('open', !isOpen);
}

function askFollowUp(btn) {
    const input = document.getElementById('chatInput');
    input.focus();
    input.placeholder = 'Ask a follow-up…';
}

function closeModal(id) {
    const modal = document.getElementById('modal-' + id);
    if (modal) modal.classList.remove('open');
}

function showPolicyRef(btn, encoded) {
    try {
        const policies = JSON.parse(decodeURIComponent(encoded));
        const contentDiv = document.getElementById('policyRefContent');
        contentDiv.innerHTML = '';
        
        if (policies.length === 0) {
            contentDiv.innerHTML = '<div class="policy-item-body">No specific policies referenced.</div>';
        } else {
            policies.forEach(p => {
                const item = document.createElement('div');
                item.className = 'policy-item';
                item.innerHTML = `
                    <div class="policy-item-title">${escHtml(p.policy_id)} v${escHtml(p.version || '1')}</div>
                    <div class="policy-item-body">${escHtml(p.content || 'Details loaded via reasoning engine.')}</div>
                `;
                contentDiv.appendChild(item);
            });
        }
        
        document.getElementById('modal-policyRef').classList.add('open');
    } catch (e) {
        console.error(e);
        alert('Policy reference data unavailable.');
    }
}

// ============ UTILS ============
function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatAnswer(text) {
    return escHtml(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/^(•|-)\s(.+)$/gm, '<span style="display:block;padding-left:12px">• $2</span>');
}

function encodePolicies(policies) {
    try {
        return encodeURIComponent(JSON.stringify(policies));
    } catch { return '[]'; }
}
