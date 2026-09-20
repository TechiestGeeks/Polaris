// ── State ──────────────────────────────────────────────────────────
let adminSession = null;
let allEmployees = [], allVendors = [], allPolicies = [], allEscalations = [];
let currentDashTab = 'employees';
const PAGE_SIZE = 8;
let pages = { employees: 1, vendors: 1, policies: 1, escalations: 1 };
let filteredEmployees = null, filteredVendors = null, filteredPolicies = null, filteredEscalations = null;

// ── Init ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const saved = sessionStorage.getItem('polaris_admin');
    if (saved) {
        adminSession = JSON.parse(saved);
        showAdminApp();
    }

    document.getElementById('adminDate').textContent =
        new Date().toLocaleDateString('en-US', { weekday:'long', year:'numeric', month:'long', day:'numeric' }) +
        '\nKeep building a compliant workplace.';

    document.getElementById('adminPass').addEventListener('keydown', e => { if (e.key==='Enter') adminLogin(); });
    document.getElementById('adminUser').addEventListener('keydown', e => { if (e.key==='Enter') document.getElementById('adminPass').focus(); });

    document.addEventListener('click', e => {
        if (!e.target.closest('.admin-dropdown-wrap')) document.getElementById('adminDropdown').classList.remove('open');
        if (!e.target.closest('.action-menu-wrap')) document.querySelectorAll('.action-menu').forEach(m => m.classList.remove('open'));
    });
});

// ── Auth ───────────────────────────────────────────────────────────
async function adminLogin() {
    const u = document.getElementById('adminUser').value.trim();
    const p = document.getElementById('adminPass').value;
    const err = document.getElementById('adminLoginError');
    const btn = document.getElementById('adminLoginBtn');

    if (!u || !p) { showErr(err, 'Please enter credentials.'); return; }

    btn.disabled = true;
    btn.textContent = 'Signing in…';
    err.style.display = 'none';

    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Invalid credentials');

        adminSession = data;
        sessionStorage.setItem('polaris_admin', JSON.stringify(adminSession));
        showAdminApp();
    } catch(e) {
        showErr(err, e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign in as Admin';
    }
}

function adminLogout() {
    adminSession = null;
    sessionStorage.removeItem('polaris_admin');
    document.getElementById('adminLogin').style.display = 'flex';
    document.getElementById('adminApp').style.display = 'none';
}

function showErr(el, msg) { el.textContent = msg; el.style.display = 'block'; }

function showAdminApp() {
    document.getElementById('adminLogin').style.display = 'none';
    document.getElementById('adminApp').style.display = 'block';
    loadStats();
    loadAll();
}

// ── API Loaders ─────────────────────────────────────────────────────
async function loadStats() {
    const data = await api('/api/admin/stats');
    document.getElementById('stat-emp').textContent = data.employees;
    document.getElementById('stat-ven').textContent = data.vendors;
    document.getElementById('stat-ven-active').textContent = `↑ ${data.active_vendors} active`;
    document.getElementById('stat-pol').textContent = data.policies;
}

async function loadAll() {
    [allEmployees, allVendors, allPolicies, allEscalations] = await Promise.all([
        api('/api/admin/employees'),
        api('/api/admin/vendors'),
        api('/api/admin/policies'),
        api('/api/admin/escalations')
    ]);
    filteredEmployees = null; filteredVendors = null; filteredPolicies = null; filteredEscalations = null;
    renderDashTab(currentDashTab);
    renderEmpTable();
    renderVendorTable();
    renderPolicyTable();
    renderEscalationTable();
}

async function api(url, opts={}) {
    const res = await fetch(url, { headers: { 'Content-Type': 'application/json', 'bypass-tunnel-reminder': 'true' }, ...opts });
    if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Request failed'); }
    return res.json();
}

// ── Navigation ──────────────────────────────────────────────────────
function switchView(name, el) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('[id^="view-"]').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${name}`).classList.add('active');
}

function switchDashTab(name, el) {
    currentDashTab = name;
    el.closest('.tab-bar').querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    renderDashTab(name);
}

function renderDashTab(name) {
    const el = document.getElementById('dashTableContent');
    const titles = { employees: ['Employees', 'View and manage employee records'], vendors: ['Vendors', 'Manage vendor partnerships'], policies: ['Policies', 'All active policy rules'] };
    document.getElementById('dashTableTitle').textContent = titles[name][0];
    document.getElementById('dashTableSub').textContent = titles[name][1];
    if (name === 'employees') el.innerHTML = buildEmpTable((filteredEmployees||allEmployees).slice(0,8), true, allEmployees.length);
    if (name === 'vendors')   el.innerHTML = buildVendorTable((filteredVendors||allVendors).slice(0,8), true, allVendors.length);
    if (name === 'policies')  el.innerHTML = buildPolicyTable((filteredPolicies||allPolicies).slice(0,8), true, allPolicies.length);
}

function toggleAdminDropdown() {
    document.getElementById('adminDropdown').classList.toggle('open');
}

// ── Global Search ────────────────────────────────────────────────────
function handleGlobalSearch(q) {
    if (!q) { renderDashTab(currentDashTab); return; }
    q = q.toLowerCase();
    const fe = allEmployees.filter(e => e.name.toLowerCase().includes(q) || e.department.toLowerCase().includes(q) || e.role.toLowerCase().includes(q));
    const fv = allVendors.filter(v => v.name.toLowerCase().includes(q) || v.category.toLowerCase().includes(q));
    const fp = allPolicies.filter(p => p.policy_id.toLowerCase().includes(q) || p.content.toLowerCase().includes(q));
    const el = document.getElementById('dashTableContent');
    el.innerHTML = (fe.length ? buildEmpTable(fe, true, fe.length) : '') +
                   (fv.length ? `<div style="padding:14px 24px 0;font-size:11px;font-weight:600;letter-spacing:.08em;color:var(--text-m);text-transform:uppercase;">Vendors</div>` + buildVendorTable(fv, true, fv.length) : '') +
                   (fp.length ? `<div style="padding:14px 24px 0;font-size:11px;font-weight:600;letter-spacing:.08em;color:var(--text-m);text-transform:uppercase;">Policies</div>` + buildPolicyTable(fp, true, fp.length) : '') +
                   (!fe.length && !fv.length && !fp.length ? `<div class="empty-state">No results for "${q}"</div>` : '');
}

// ── Table Builders ────────────────────────────────────────────────────

const AVATAR_COLORS = ['#2563eb','#059669','#d97706','#db2777','#7c3aed','#0d9488','#dc2626','#2563eb'];
function avatarColor(name) { let h=0; for(let c of name) h+=c.charCodeAt(0); return AVATAR_COLORS[h%AVATAR_COLORS.length]; }
function initials(name) { return name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase(); }

function buildPagination(total, page, key, mini) {
    if (mini || total <= PAGE_SIZE) return `<div class="table-pagination"><span>Showing ${Math.min(page * PAGE_SIZE, total)} of ${total} records</span></div>`;
    const totalPages = Math.ceil(total / PAGE_SIZE);
    const start = (page - 1) * PAGE_SIZE + 1;
    const end   = Math.min(page * PAGE_SIZE, total);
    let nums = [];
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || Math.abs(i - page) <= 1) nums.push(i);
        else if (nums[nums.length - 1] !== '...') nums.push('...');
    }
    const btns = nums.map(n => n === '...'
        ? `<span class="page-btn" style="cursor:default;pointer-events:none">…</span>`
        : `<button class="page-btn ${n === page ? 'active' : ''}" data-page="${n}" data-key="${key}">${n}</button>`
    ).join('');
    return `<div class="table-pagination">
        <span>Showing ${start}–${end} of ${total}</span>
        <div class="page-btns">
            <button class="page-btn" data-page="${page - 1}" data-key="${key}" ${page <= 1 ? 'disabled style="opacity:.3"' : ''}>‹</button>
            ${btns}
            <button class="page-btn" data-page="${page + 1}" data-key="${key}" ${page >= totalPages ? 'disabled style="opacity:.3"' : ''}>›</button>
        </div>
    </div>`;
}

// Delegated pagination click handler — survives innerHTML re-renders
document.addEventListener('click', e => {
    const btn = e.target.closest('button[data-key]');
    if (!btn || btn.disabled) return;
    const key = btn.dataset.key;
    const p   = parseInt(btn.dataset.page);
    if (!key || isNaN(p)) return;
    const totals = {
        employees: (filteredEmployees || allEmployees).length,
        vendors:   (filteredVendors   || allVendors).length,
        policies:  (filteredPolicies  || allPolicies).length,
        escalations: (filteredEscalations || allEscalations).length
    };
    const max = Math.ceil((totals[key] || 1) / PAGE_SIZE);
    pages[key] = Math.max(1, Math.min(p, max));
    if (key === 'employees') renderEmpTable();
    if (key === 'vendors')   renderVendorTable();
    if (key === 'policies')  renderPolicyTable();
    if (key === 'escalations') renderEscalationTable();
});

function buildEmpTable(data, mini=false, total=null) {
    const rows = data.map(e => `
        <tr>
            <td><div class="emp-cell">
                <div class="emp-avatar" style="background:${avatarColor(e.name)}">${initials(e.name)}</div>
                <div><div class="emp-name">${e.name}</div><div class="emp-email">${e.employee_id.toLowerCase()}@apexnova.com</div></div>
            </div></td>
            <td>${e.employee_id}</td>
            <td>${e.department}</td>
            <td>${e.role}</td>
            <td><span class="access-badge">${e.access_level}</span></td>
            <td>${e.region}</td>
            ${mini ? '' : `<td>
                <div class="action-menu-wrap">
                    <button class="action-btn" onclick="toggleMenu('menu-${e.employee_id}')">⋯</button>
                    <div class="action-menu" id="menu-${e.employee_id}">
                        <div class="action-menu-item" onclick="openUpgrade('${e.employee_id}','${e.name}','${e.role}','${e.access_level}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 11 12 6 7 11"/><polyline points="17 18 12 13 7 18"/></svg> Upgrade / Downgrade
                        </div>
                        <div class="action-menu-item danger" onclick="deleteEmployee('${e.employee_id}','${e.name}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg> Remove
                        </div>
                    </div>
                </div>
            </td>`}
        </tr>`).join('');
    const t = total ?? (filteredEmployees||allEmployees).length;
    return `
        <table class="data-table" id="emp-data-table">
            <thead><tr>
                <th>NAME</th><th>EMPLOYEE ID</th><th>DEPARTMENT</th><th>ROLE</th><th>ACCESS LEVEL</th><th>REGION</th>
                ${mini ? '' : '<th>ACTIONS</th>'}
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>
        ${buildPagination(t, pages.employees, 'employees', mini)}`;
}

function buildVendorTable(data, mini=false, total=null) {
    const rows = data.map(v => `
        <tr>
            <td><div class="emp-cell">
                <div class="emp-avatar" style="background:${avatarColor(v.name)}">${initials(v.name)}</div>
                <div><div class="emp-name">${v.name}</div><div class="emp-email">${v.contact}</div></div>
            </div></td>
            <td>${v.vendor_id}</td>
            <td>${v.category}</td>
            <td>${v.region}</td>
            <td><span class="badge ${v.status==='Active'?'badge-active':v.status==='Under Review'?'badge-review':'badge-inactive'}">${v.status}</span></td>
            <td>${v.contract_end||'—'}</td>
            ${mini ? '' : `<td>
                <div class="action-menu-wrap">
                    <button class="action-btn" onclick="toggleMenu('menu-${v.vendor_id}')">⋯</button>
                    <div class="action-menu" id="menu-${v.vendor_id}">
                        <div class="action-menu-item danger" onclick="deleteVendor('${v.vendor_id}','${v.name}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg> Remove
                        </div>
                    </div>
                </div>
            </td>`}
        </tr>`).join('');
    const t = total ?? (filteredVendors||allVendors).length;
    return `
        <table class="data-table">
            <thead><tr>
                <th>NAME</th><th>VENDOR ID</th><th>CATEGORY</th><th>REGION</th><th>STATUS</th><th>CONTRACT END</th>
                ${mini ? '' : '<th>ACTIONS</th>'}
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>
        ${buildPagination(t, pages.vendors, 'vendors', mini)}`;
}

function buildPolicyTable(data, mini=false, total=null) {
    const rows = data.map(p => `
        <tr>
            <td style="font-family:monospace;font-size:12px;color:var(--text-p);font-weight:600;">${p.policy_id}</td>
            <td><span class="badge ${p.policy_type==='standard'?'badge-standard':p.policy_type==='exception'?'badge-exception':'badge-regional'}">${p.policy_type}</span></td>
            <td style="max-width:280px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p.content}</td>
            <td>${p.region||'GLOBAL'}</td>
            <td>${p.role||'ALL'}</td>
            <td style="font-weight:600;color:var(--text-p);">${p.priority}</td>
            ${mini ? '' : `<td>
                <div class="action-menu-wrap">
                    <button class="action-btn" onclick="toggleMenu('menu-pol-${p.policy_id.replace(/[^a-z0-9]/gi,'_')}')">⋯</button>
                    <div class="action-menu" id="menu-pol-${p.policy_id.replace(/[^a-z0-9]/gi,'_')}">
                        <div class="action-menu-item danger" onclick="deletePolicy('${p.policy_id}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg> Delete
                        </div>
                    </div>
                </div>
            </td>`}
        </tr>`).join('');
    const t = total ?? (filteredPolicies||allPolicies).length;
    return `
        <table class="data-table">
            <thead><tr>
                <th>POLICY ID</th><th>TYPE</th><th>CONTENT</th><th>REGION</th><th>ROLE</th><th>PRIORITY</th>
                ${mini ? '' : '<th>ACTIONS</th>'}
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>
        ${buildPagination(t, pages.policies, 'policies', mini)}`;
}

function buildEscalationTable(data, mini=false, total=null) {
    const rows = data.map(e => {
        const isPending = e.status === 'Pending';
        return `
        <tr>
            <td style="font-family:monospace;font-size:12px;color:var(--text-p);font-weight:600;">${e.id}</td>
            <td>
                <div class="emp-cell">
                    <div class="emp-avatar" style="background:${avatarColor(e.employee_name)}">${initials(e.employee_name)}</div>
                    <div><div class="emp-name">${e.employee_name}</div><div class="emp-email">${e.employee_id}</div></div>
                </div>
            </td>
            <td style="max-width:300px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${e.question}</td>
            <td><span class="badge ${isPending ? 'badge-review' : 'badge-active'}">${e.status}</span></td>
            <td>${new Date(e.timestamp).toLocaleDateString()}</td>
            <td>
                ${isPending ? `<button class="btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="openResolveModal('${e.id}')">Resolve</button>` : `<span style="font-size:12px;color:var(--text-s)">Resolved</span>`}
            </td>
        </tr>`;
    }).join('');
    const t = total ?? (filteredEscalations||allEscalations).length;
    return `
        <table class="data-table">
            <thead><tr>
                <th>TICKET ID</th><th>EMPLOYEE</th><th>ISSUE</th><th>STATUS</th><th>DATE</th><th>ACTIONS</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>
        ${buildPagination(t, pages.escalations, 'escalations', mini)}`;
}

// ── Full Table Renderers ───────────────────────────────────────────
function renderEmpTable() {
    const data = filteredEmployees || allEmployees;
    const page = pages.employees;
    const slice = data.slice((page-1)*PAGE_SIZE, page*PAGE_SIZE);
    document.getElementById('empTable').innerHTML = buildEmpTable(slice, false, data.length);
}
function renderVendorTable() {
    const data = filteredVendors || allVendors;
    const page = pages.vendors;
    const slice = data.slice((page-1)*PAGE_SIZE, page*PAGE_SIZE);
    document.getElementById('vendorTable').innerHTML = buildVendorTable(slice, false, data.length);
}
function renderPolicyTable() {
    const data = filteredPolicies || allPolicies;
    const page = pages.policies;
    const slice = data.slice((page-1)*PAGE_SIZE, page*PAGE_SIZE);
    document.getElementById('policyTable').innerHTML = buildPolicyTable(slice, false, data.length);
}
function renderEscalationTable() {
    const data = filteredEscalations || allEscalations;
    const page = pages.escalations;
    const slice = data.slice((page-1)*PAGE_SIZE, page*PAGE_SIZE);
    document.getElementById('escalationTable').innerHTML = buildEscalationTable(slice, false, data.length);
}

// ── Inline Filters ────────────────────────────────────────────────
function filterEmpTable(q) {
    filteredEmployees = q ? allEmployees.filter(e => JSON.stringify(e).toLowerCase().includes(q.toLowerCase())) : null;
    pages.employees = 1;
    renderEmpTable();
}
function filterVendorTable(q) {
    filteredVendors = q ? allVendors.filter(v => JSON.stringify(v).toLowerCase().includes(q.toLowerCase())) : null;
    pages.vendors = 1;
    renderVendorTable();
}
function filterPolicyTable(q) {
    filteredPolicies = q ? allPolicies.filter(p => JSON.stringify(p).toLowerCase().includes(q.toLowerCase())) : null;
    pages.policies = 1;
    renderPolicyTable();
}

// ── Action Menus ──────────────────────────────────────────────────
function toggleMenu(id) {
    document.querySelectorAll('.action-menu').forEach(m => { if (m.id!==id) m.classList.remove('open'); });
    document.getElementById(id)?.classList.toggle('open');
}

// ── Modals ────────────────────────────────────────────────────────
function openModal(name) {
    document.getElementById(`modal-${name}`).classList.add('open');
}
function closeModal(name) {
    document.getElementById(`modal-${name}`).classList.remove('open');
}

// Close on backdrop click
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.classList.remove('open');
    }
});

// ── Add Employee ──────────────────────────────────────────────────
async function saveEmployee() {
    const btn = document.getElementById('emp-save-btn');
    const err = document.getElementById('emp-err');
    const name = document.getElementById('emp-name').value.trim();
    if (!name) { showErr(err, 'Name is required.'); return; }

    btn.disabled = true; btn.textContent = 'Saving…';
    try {
        const emp = await api('/api/admin/employees', {
            method: 'POST',
            body: JSON.stringify({
                name,
                department: document.getElementById('emp-dept').value,
                region: document.getElementById('emp-region').value,
                role: document.getElementById('emp-role').value,
                access_level: document.getElementById('emp-access').value
            })
        });
        allEmployees.push(emp);
        renderEmpTable(allEmployees);
        renderDashTab(currentDashTab);
        loadStats();
        closeModal('addEmployee');
        document.getElementById('emp-name').value = '';
        err.style.display='none';
    } catch(e) { showErr(err, e.message); }
    finally { btn.disabled=false; btn.textContent='Add Employee'; }
}

// ── Upgrade/Downgrade ─────────────────────────────────────────────
function openUpgrade(id, name, role, access) {
    document.getElementById('upgrade-emp-id').value = id;
    document.getElementById('upgrade-title').textContent = `Update: ${name}`;
    document.getElementById('upgrade-sub').textContent = `Current: ${role} · ${access}`;
    document.getElementById('upgrade-role').value = role;
    document.getElementById('upgrade-access').value = access;
    openModal('upgradeEmployee');
}

async function saveUpgrade() {
    const id = document.getElementById('upgrade-emp-id').value;
    const err = document.getElementById('upgrade-err');
    try {
        const updated = await api(`/api/admin/employees/${id}`, {
            method: 'PATCH',
            body: JSON.stringify({
                role: document.getElementById('upgrade-role').value,
                access_level: document.getElementById('upgrade-access').value
            })
        });
        const idx = allEmployees.findIndex(e => e.employee_id === id);
        if (idx >= 0) allEmployees[idx] = updated;
        renderEmpTable(allEmployees);
        renderDashTab(currentDashTab);
        closeModal('upgradeEmployee');
    } catch(e) { showErr(err, e.message); }
}

// ── Delete Employee ───────────────────────────────────────────────
async function deleteEmployee(id, name) {
    if (!confirm(`Remove ${name} from POLARIS? This cannot be undone.`)) return;
    try {
        await api(`/api/admin/employees/${id}`, { method: 'DELETE' });
        allEmployees = allEmployees.filter(e => e.employee_id !== id);
        renderEmpTable(allEmployees);
        renderDashTab(currentDashTab);
        loadStats();
    } catch(e) { alert('Error: ' + e.message); }
}

// ── Add Policy ────────────────────────────────────────────────────
async function savePolicy() {
    const btn = document.getElementById('pol-save-btn');
    const err = document.getElementById('pol-err');
    const pid = document.getElementById('pol-id').value.trim().toUpperCase().replace(/\s+/g,'-');
    const content = document.getElementById('pol-content').value.trim();
    if (!pid || !content) { showErr(err,'Policy ID and content are required.'); return; }

    btn.disabled=true; btn.textContent='Creating…';
    try {
        const pol = await api('/api/admin/policies', {
            method: 'POST',
            body: JSON.stringify({
                policy_id: pid,
                content,
                policy_type: document.getElementById('pol-type').value,
                priority: parseInt(document.getElementById('pol-priority').value),
                region: document.getElementById('pol-region').value,
                role: document.getElementById('pol-role').value,
                vendor: document.getElementById('pol-vendor').value || 'ALL',
                department: 'ALL', access_level: 'ALL', data_type: 'ALL',
                dataset: 'ALL', version: '1.0', supersedes: null, expiration_date: null
            })
        });
        allPolicies.unshift(pol);
        renderPolicyTable(allPolicies);
        renderDashTab(currentDashTab);
        loadStats();
        closeModal('addPolicy');
        document.getElementById('pol-id').value=''; document.getElementById('pol-content').value='';
        err.style.display='none';
    } catch(e) { showErr(err, e.message); }
    finally { btn.disabled=false; btn.textContent='Create Policy'; }
}

// ── Delete Policy ─────────────────────────────────────────────────
async function deletePolicy(id) {
    if (!confirm(`Delete policy "${id}"? This cannot be undone.`)) return;
    try {
        await api(`/api/admin/policies/${id}`, { method: 'DELETE' });
        allPolicies = allPolicies.filter(p => p.policy_id !== id);
        renderPolicyTable(allPolicies);
        renderDashTab(currentDashTab);
        loadStats();
    } catch(e) { alert('Error: ' + e.message); }
}

// ── Add Vendor ────────────────────────────────────────────────────
async function saveVendor() {
    const btn = document.getElementById('ven-save-btn');
    const err = document.getElementById('ven-err');
    const name = document.getElementById('ven-name').value.trim();
    if (!name) { showErr(err,'Vendor name is required.'); return; }

    btn.disabled=true; btn.textContent='Adding…';
    try {
        const v = await api('/api/admin/vendors', {
            method: 'POST',
            body: JSON.stringify({
                name,
                category: document.getElementById('ven-cat').value,
                region: document.getElementById('ven-region').value,
                contact: document.getElementById('ven-contact').value,
                contract_end: document.getElementById('ven-end').value,
                compliance: document.getElementById('ven-comp').value,
                status: document.getElementById('ven-status').value
            })
        });
        allVendors.push(v);
        renderVendorTable(allVendors);
        renderDashTab(currentDashTab);
        loadStats();
        closeModal('addVendor');
        err.style.display='none';
    } catch(e) { showErr(err, e.message); }
    finally { btn.disabled=false; btn.textContent='Add Vendor'; }
}

// ── Delete Vendor ─────────────────────────────────────────────────
async function deleteVendor(id, name) {
    if (!confirm(`Remove vendor "${name}"?`)) return;
    try {
        await api(`/api/admin/vendors/${id}`, { method: 'DELETE' });
        allVendors = allVendors.filter(v => v.vendor_id !== id);
        renderVendorTable(allVendors);
        renderDashTab(currentDashTab);
        loadStats();
    } catch(e) { alert('Error: ' + e.message); }
}

// ── Resolve Escalation ─────────────────────────────────────────────
function openResolveModal(id) {
    const esc = allEscalations.find(e => e.id === id);
    if (!esc) return;
    document.getElementById('resolve-esc-id').value = id;
    document.getElementById('resolve-title').textContent = `Resolve Ticket ${id}`;
    document.getElementById('resolve-context').textContent = esc.context || esc.question;
    document.getElementById('resolve-response').value = '';
    document.getElementById('resolve-err').style.display = 'none';
    openModal('resolveEscalation');
}

async function saveResolution() {
    const id = document.getElementById('resolve-esc-id').value;
    const responseText = document.getElementById('resolve-response').value.trim();
    const btn = document.getElementById('resolve-save-btn');
    const err = document.getElementById('resolve-err');

    if (!responseText) { showErr(err, 'Resolution message is required.'); return; }

    btn.disabled = true; btn.textContent = 'Resolving…';
    try {
        const updated = await api(`/api/admin/escalations/${id}/resolve`, {
            method: 'POST',
            body: JSON.stringify({ admin_response: responseText })
        });
        const idx = allEscalations.findIndex(e => e.id === id);
        if (idx >= 0) allEscalations[idx] = updated;
        renderEscalationTable();
        closeModal('resolveEscalation');
    } catch (e) {
        showErr(err, e.message);
    } finally {
        btn.disabled = false; btn.textContent = 'Resolve';
    }
}
