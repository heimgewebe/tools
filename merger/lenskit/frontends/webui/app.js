// repoLens UI Logic

const API_BASE = '/api';

// Token handling
const TOKEN_KEY = 'rlens_token';
const SETS_KEY = 'rlens_sets';
const CONFIG_KEY = 'rlens_config';
const ATLAS_CONFIG_KEY = 'rlens_atlas_config';

// Picker state
let currentPickerTarget = null;
let currentPickerPath = null;
let currentPickerToken = null; // For token-based navigation

// Available Extras
const EXTRAS_OPTIONS = [
    'health',
    'augment_sidecar',
    'organism_index',
    'fleet_panorama',
    'json_sidecar',
    'heatmap'
];

// Default selected extras (based on existing logic/user preference)
const DEFAULT_EXTRAS = [
    'augment_sidecar',
    'json_sidecar'
];

function getToken() {
    return document.getElementById('authToken').value || localStorage.getItem(TOKEN_KEY) || '';
}

function setToken(token) {
    if (token) {
        localStorage.setItem(TOKEN_KEY, token);
    } else {
        localStorage.removeItem(TOKEN_KEY);
    }
}

// Wrapper for fetch with auth
async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = options.headers || {};

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    options.headers = headers;
    return fetch(url, options);
}

async function fetchHealth() {
    try {
        // Health check endpoint is open, but we use it to check connectivity
        const res = await apiFetch(`${API_BASE}/health`);
        const data = await res.json();
        const authStatus = data.auth_enabled ? '🔒 Auth' : '🔓 Open';
        document.getElementById('status').innerText = `v${data.version} • ${authStatus} • Hub: ${data.hub}`;

        // Only set values if empty (respect user changes or saved config)
        if (!document.getElementById('hubPath').value) {
            document.getElementById('hubPath').value = data.hub || '';
        }
        if (!document.getElementById('mergesPath').value && data.merges_dir) {
            document.getElementById('mergesPath').value = data.merges_dir || '';
        }

        return data.hub;
    } catch (e) {
        document.getElementById('status').innerText = 'Offline';
        return null;
    }
}

async function fetchRepos(hub) {
    const list = document.getElementById('repoList');
    list.innerHTML = '<div class="text-gray-500 italic">Loading repos...</div>';

    try {
        // Construct query string properly
        let url = `${API_BASE}/repos`;
        if (hub) {
            url += `?hub=${encodeURIComponent(hub)}`;
        }

        const res = await apiFetch(url);
        if (res.status === 401) {
             list.innerHTML = '<div class="text-red-400">Access Denied (Check Token)</div>';
             return;
        }
        if (res.status === 403) {
             list.innerHTML = '<div class="text-red-400">Hub path restricted</div>';
             return;
        }

        if (!res.ok) {
             list.innerHTML = '<div class="text-red-400">Error fetching repos</div>';
             return;
        }

        const repos = await res.json();

        list.innerHTML = '';
        if (repos.length === 0) {
            list.innerHTML = '<div class="text-gray-500 italic">No repos found in hub.</div>';
            return;
        }

        repos.forEach(repo => {
            const div = document.createElement('div');
            div.className = "flex items-center space-x-2 p-1 hover:bg-gray-800 rounded cursor-pointer";
            div.onclick = (e) => {
                if (e.target.type !== 'checkbox') {
                    const box = div.querySelector('input[type="checkbox"]');
                    box.checked = !box.checked;
                }
            };
            div.innerHTML = `
                <input type="checkbox" name="repos" value="${repo}" class="form-checkbox text-blue-500 bg-gray-900 border-gray-700">
                <span class="font-bold text-gray-300 select-none">${repo}</span>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        list.innerHTML = '<div class="text-red-500">Error loading repos: ' + e.message + '</div>';
    }
}

function selectAllRepos() {
    const boxes = document.querySelectorAll('input[name="repos"]');
    if (boxes.length === 0) return;

    // Check if all are currently checked
    const allChecked = Array.from(boxes).every(b => b.checked);
    // Toggle
    boxes.forEach(b => b.checked = !allChecked);
}

// --- Sets Management ---

function getSets() {
    try {
        return JSON.parse(localStorage.getItem(SETS_KEY) || '{}');
    } catch { return {}; }
}

function saveSet() {
    const name = document.getElementById('setName').value.trim();
    if (!name) return alert("Please enter a name");

    const selected = Array.from(document.querySelectorAll('input[name="repos"]:checked')).map(cb => cb.value);
    if (selected.length === 0) return alert("No repos selected");

    const sets = getSets();
    sets[name] = selected;
    localStorage.setItem(SETS_KEY, JSON.stringify(sets));
    document.getElementById('setName').value = '';
    renderSets();
}

function deleteSet(name) {
    if (!confirm(`Delete set "${name}"?`)) return;
    const sets = getSets();
    delete sets[name];
    localStorage.setItem(SETS_KEY, JSON.stringify(sets));
    renderSets();
}

function loadSet(name) {
    const sets = getSets();
    const repos = sets[name];
    if (!repos) return;

    const boxes = document.querySelectorAll('input[name="repos"]');
    boxes.forEach(b => {
        b.checked = repos.includes(b.value);
    });
}

function renderSets() {
    const div = document.getElementById('setsList');
    const sets = getSets();
    div.innerHTML = '';

    Object.keys(sets).sort().forEach(name => {
        const badge = document.createElement('div');
        badge.className = "flex items-center bg-gray-700 hover:bg-gray-600 rounded px-2 py-1 text-xs cursor-pointer";
        badge.onclick = () => loadSet(name);

        const span = document.createElement('span');
        span.innerText = name;
        span.className = "mr-2 text-blue-300 font-bold";

        const del = document.createElement('span');
        del.innerHTML = '&times;';
        del.className = "text-gray-400 hover:text-red-400 font-bold";
        del.onclick = (e) => {
            e.stopPropagation();
            deleteSet(name);
        };

        badge.appendChild(span);
        badge.appendChild(del);
        div.appendChild(badge);
    });
}

// --- Config Management ---

function saveConfig() {
    const config = {
        profile: document.getElementById('profile').value,
        mode: document.getElementById('mode').value,
        splitSize: document.getElementById('splitSize').value,
        maxBytes: document.getElementById('maxBytes').value,
        planOnly: document.getElementById('planOnly').checked,
        codeOnly: document.getElementById('codeOnly').checked,
        pathFilter: document.getElementById('pathFilter').value,
        extFilter: document.getElementById('extFilter').value,
        extras: Array.from(document.querySelectorAll('input[name="extras"]:checked')).map(cb => cb.value),
        // Persist paths too if desired
        hubPath: document.getElementById('hubPath').value,
        mergesPath: document.getElementById('mergesPath').value
    };
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config));

    const btn = document.querySelector('button[onclick="saveConfig()"]');
    const oldText = btn.innerText;
    btn.innerText = "Saved!";
    setTimeout(() => btn.innerText = oldText, 1000);
}

function restoreConfig() {
    try {
        const config = JSON.parse(localStorage.getItem(CONFIG_KEY));
        if (!config) return;

        if (config.profile) document.getElementById('profile').value = config.profile;
        if (config.mode) document.getElementById('mode').value = config.mode;
        if (config.splitSize) document.getElementById('splitSize').value = config.splitSize;
        if (config.maxBytes) document.getElementById('maxBytes').value = config.maxBytes;
        if (config.planOnly !== undefined) document.getElementById('planOnly').checked = config.planOnly;
        if (config.codeOnly !== undefined) document.getElementById('codeOnly').checked = config.codeOnly;
        if (config.pathFilter !== undefined) document.getElementById('pathFilter').value = config.pathFilter;
        if (config.extFilter !== undefined) document.getElementById('extFilter').value = config.extFilter;

        if (config.hubPath) document.getElementById('hubPath').value = config.hubPath;
        if (config.mergesPath) document.getElementById('mergesPath').value = config.mergesPath;

        // Extras need to be handled carefully as they are rendered async or statically
        if (config.extras) {
             const boxes = document.querySelectorAll('input[name="extras"]');
             boxes.forEach(b => {
                 b.checked = config.extras.includes(b.value);
             });
        }

        // Restore Atlas Config
        const atlasConfig = JSON.parse(localStorage.getItem(ATLAS_CONFIG_KEY));
        if (atlasConfig) {
             if (atlasConfig.root) document.getElementById('atlasRoot').value = atlasConfig.root;
             if (atlasConfig.depth) document.getElementById('atlasDepth').value = atlasConfig.depth;
             if (atlasConfig.limit) document.getElementById('atlasLimit').value = atlasConfig.limit;
             if (atlasConfig.excludes) document.getElementById('atlasExcludes').value = atlasConfig.excludes;
        }

    } catch (e) { console.error("Error restoring config", e); }
}

function renderExtras() {
    const container = document.getElementById('extras-container');
    container.innerHTML = '';

    EXTRAS_OPTIONS.forEach(opt => {
        const isChecked = DEFAULT_EXTRAS.includes(opt);
        const label = document.createElement('label');
        label.className = "flex items-center space-x-2 cursor-pointer text-xs";
        label.innerHTML = `
            <input type="checkbox" name="extras" value="${opt}" ${isChecked ? 'checked' : ''} class="form-checkbox text-blue-500 bg-gray-900 border-gray-700">
            <span>${opt}</span>
        `;
        container.appendChild(label);
    });
}

// --- Folder Picker ---

async function openPicker(targetId) {
    currentPickerTarget = targetId;
    document.getElementById('pickerModal').classList.remove('hidden');
    await loadPickerRoots();
}

function closePicker() {
    document.getElementById('pickerModal').classList.add('hidden');
    currentPickerTarget = null;
    currentPickerPath = null;
    currentPickerToken = null;
}

function applyPickerSelection() {
    if (!currentPickerTarget) return;

    // Store token (opaque) in data attribute if target supports it (e.g. Atlas),
    // or value if appropriate.
    // For Atlas, we need to send the token.
    // For Hub (Legacy/JobRequest), we typically send the path string.
    // BUT: The goal is to satisfy CodeQL. Hub config is less dynamic.
    // Let's adopt a hybrid approach:
    // 1. Set visible value to path (for user confirmation/display)
    // 2. Set 'data-token' attribute on the input to the token.
    // Consumers (startAtlasJob) will check for data-token.

    const el = document.getElementById(currentPickerTarget);
    if (el) {
        el.value = currentPickerPath || '';
        el.dataset.token = currentPickerToken || '';
    }

    closePicker();
}

async function loadPickerRoots() {
    const list = document.getElementById('pickerList');
    const pathDisplay = document.getElementById('pickerCurrentPath');
    pathDisplay.value = "Select Root";
    list.innerHTML = '<div class="text-gray-500 italic">Loading roots...</div>';

    try {
        const res = await apiFetch(`${API_BASE}/fs/roots`);
        if (!res.ok) throw new Error("Fetch roots failed");
        const data = await res.json();

        list.innerHTML = '';
        data.roots.forEach(r => {
            const div = document.createElement('div');
            div.className = "flex items-center cursor-pointer hover:bg-gray-700 p-1 rounded";
            div.onclick = () => loadPickerToken(r.token);

            let label = r.id.toUpperCase();
            let desc = r.path;

            div.innerHTML = `<span class="mr-2">🏠</span> <span class="font-bold text-blue-300 mr-2">${label}</span> <span class="text-gray-500 text-xs truncate">${desc}</span>`;
            list.appendChild(div);
        });
    } catch (e) {
        list.innerHTML = `<div class="text-red-400">Error: ${e.message}</div>`;
    }
}

async function loadPickerToken(token) {
    const list = document.getElementById('pickerList');
    const pathDisplay = document.getElementById('pickerCurrentPath');
    list.innerHTML = '<div class="text-gray-500 italic">Loading...</div>';

    try {
        // Use token navigation
        const url = `${API_BASE}/fs/list?token=${encodeURIComponent(token)}`;
        const res = await apiFetch(url);

        if (res.status === 403) throw new Error("Access Denied (Path restricted)");
        if (!res.ok) throw new Error("Fetch failed");

        const data = await res.json();

        // Update state
        currentPickerPath = data.abs;
        currentPickerToken = token;
        pathDisplay.value = data.abs;

        // Add "Use This Folder" button at the top
        list.innerHTML = `
            <div class="p-2 border-b border-gray-700 flex justify-between items-center bg-gray-800 sticky top-0">
                <span class="text-xs text-gray-400 font-mono truncate mr-2">${data.abs}</span>
                <button onclick="applyPickerSelection()" class="bg-green-600 hover:bg-green-500 text-white px-3 py-1 rounded text-xs font-bold">Use This Folder</button>
            </div>
        `;

        // Add "Up" button if parent_token exists
        if (data.parent_token) {
            const upDiv = document.createElement('div');
            upDiv.className = "flex items-center cursor-pointer hover:bg-gray-700 p-1 rounded mb-1 border-b border-gray-700";
            upDiv.onclick = () => loadPickerToken(data.parent_token);
            upDiv.innerHTML = `<span class="mr-2">⬆️</span> <span>..</span>`;
            list.appendChild(upDiv);
        } else {
            // "Up" to Roots list
            const upDiv = document.createElement('div');
            upDiv.className = "flex items-center cursor-pointer hover:bg-gray-700 p-1 rounded mb-1 border-b border-gray-700";
            upDiv.onclick = () => loadPickerRoots();
            upDiv.innerHTML = `<span class="mr-2">🏠</span> <span>Roots</span>`;
            list.appendChild(upDiv);
        }

        data.entries.forEach(entry => {
            const div = document.createElement('div');
            div.className = "flex items-center cursor-pointer hover:bg-gray-700 p-1 rounded";

            if (entry.type === 'dir') {
                // Directory: Click to navigate
                div.onclick = () => loadPickerToken(entry.token);
                div.innerHTML = `<span class="mr-2">📁</span> <span>${entry.name}</span>`;
            } else {
                // File: Non-clickable in folder picker mode (or select?)
                div.className += " text-gray-500 cursor-default";
                div.innerHTML = `<span class="mr-2">📄</span> <span>${entry.name}</span>`;
            }
            list.appendChild(div);
        });

    } catch (e) {
        list.innerHTML = `<div class="text-red-400">Error: ${e.message}</div>`;
    }
}

function pickerSelect() {
    if (currentPickerTarget && currentPickerPath) {
        document.getElementById(currentPickerTarget).value = currentPickerPath;

        // If hub changed, reload repos
        if (currentPickerTarget === 'hubPath') {
            fetchRepos(currentPickerPath);
        }

        closePicker();
    }
}

async function loadArtifacts() {
    const list = document.getElementById('artifactList');
    list.innerHTML = '<div class="text-gray-500 italic">Loading...</div>';
    try {
        const res = await apiFetch(`${API_BASE}/artifacts`);
        if (res.status === 401) {
             list.innerHTML = '<div class="text-red-400">Auth Required</div>';
             return;
        }
        const arts = await res.json();

        list.innerHTML = '';
        if (arts.length === 0) {
            list.innerHTML = '<div class="text-gray-500 italic">No artifacts yet.</div>';
            return;
        }

        arts.forEach(art => {
            const div = document.createElement('div');
            div.className = "bg-gray-900 p-2 rounded border border-gray-700 flex flex-col";

            const date = new Date(art.created_at).toLocaleString();
            const repos = art.repos.length > 3 ? `${art.repos.slice(0,3).join(', ')} +${art.repos.length-3}` : art.repos.join(', ');

            let links = [];

            // Handle known keys explicitly, then others
            // Primary JSON
            if (art.paths.json) {
                links.push(`<button data-dl="${API_BASE}/artifacts/${art.id}/download?key=json" data-name="${art.paths.json}" class="text-green-400 hover:underline">JSON</button>`);
            }
            // Canonical MD
            if (art.paths.md) {
                links.push(`<button data-dl="${API_BASE}/artifacts/${art.id}/download?key=md" data-name="${art.paths.md}" class="text-blue-400 hover:underline">Markdown</button>`);
            }
            // Other parts
            for (const [key, val] of Object.entries(art.paths)) {
                if (key !== 'json' && key !== 'md' && key !== 'canonical_md' && key !== 'index_json') {
                    // Try to be smart about parts
                    if (key.startsWith('md_part')) {
                         links.push(`<button data-dl="${API_BASE}/artifacts/${art.id}/download?key=${key}" data-name="${val}" class="text-gray-400 hover:underline text-xs">Part ${key.split('_').pop()}</button>`);
                    }
                }
            }

            div.innerHTML = `
                <div class="flex justify-between items-start">
                    <span class="font-bold text-blue-300">${art.params.level} / ${art.params.mode}</span>
                    <span class="text-xs text-gray-500">${date}</span>
                </div>
                <div class="text-xs text-gray-400 truncate mb-1" title="${art.repos.join(', ')}">${repos || 'All Repos'}</div>
                <div class="flex flex-wrap gap-2 text-xs mt-1">
                    ${links.join(' <span class="text-gray-600">|</span> ')}
                </div>
            `;
            list.appendChild(div);
        });

    } catch (e) {
        list.innerHTML = '<div class="text-red-500">Error loading artifacts.</div>';
    }

    // Wire download buttons
    list.querySelectorAll('button[data-dl]').forEach(btn => {
        btn.addEventListener('click', async () => {
            try {
                const url = btn.getAttribute('data-dl');
                const name = btn.getAttribute('data-name') || 'artifact';
                // Use the updated function for secure downloads
                await downloadWithAuth(url, name);
            } catch (e) {
                alert(e.message);
            }
        });
    });
}

async function startJob(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerText = "Starting...";

    // Dynamically query selected repos from the DOM
    const selectedRepos = Array.from(document.querySelectorAll('input[name="repos"]:checked')).map(cb => cb.value);

    // Extensions
    const extRaw = document.getElementById('extFilter').value.trim();
    const extensions = extRaw ? extRaw.split(',').map(s => s.trim()) : null;

    // Extras
    const checkedExtras = Array.from(document.querySelectorAll('input[name="extras"]:checked')).map(cb => cb.value);
    const extrasCsv = checkedExtras.join(',');

    // JSON Sidecar legacy logic
    const jsonSidecar = checkedExtras.includes('json_sidecar');

    const payload = {
        hub: document.getElementById('hubPath').value,
        merges_dir: document.getElementById('mergesPath').value || null,
        repos: selectedRepos.length > 0 ? selectedRepos : null,
        level: document.getElementById('profile').value,
        mode: document.getElementById('mode').value,
        max_bytes: document.getElementById('maxBytes').value,
        split_size: document.getElementById('splitSize').value,
        plan_only: document.getElementById('planOnly').checked,
        code_only: document.getElementById('codeOnly').checked,
        json_sidecar: jsonSidecar,
        path_filter: document.getElementById('pathFilter').value.trim() || null,
        extensions: extensions,
        extras: extrasCsv
    };

    try {
        const res = await apiFetch(`${API_BASE}/jobs`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        if (res.status === 401) {
            throw new Error("Unauthorized. Please check your token.");
        }

        if (!res.ok) {
            throw new Error(`HTTP Error ${res.status}`);
        }

        const job = await res.json();

        btn.disabled = false;
        btn.innerText = "Start Job";

        // Start log streaming
        streamLogs(job.id);

    } catch (e) {
        alert("Failed to start job: " + e.message);
        btn.disabled = false;
        btn.innerText = "Start Job";
    }
}

function streamLogs(jobId) {
    const pre = document.getElementById('logs');
    pre.innerText = `Connecting to logs for job ${jobId}...\n`;

    const token = getToken();
    const url = `${API_BASE}/jobs/${jobId}/logs` + (token ? `?token=${encodeURIComponent(token)}` : '');
    const es = new EventSource(url);

    es.onmessage = (event) => {
        if (event.data === 'end') {
            es.close();
            pre.innerText += "\n[Job Finished]\n";
            loadArtifacts(); // Refresh artifacts
            return;
        }
        pre.innerText += event.data + "\n";
        pre.scrollTop = pre.scrollHeight;
    };

    es.onerror = () => {
        pre.innerText += "\n[Connection Lost]\n";
        es.close();
    };
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
    // Render extras immediately
    renderExtras();
    renderSets();
    restoreConfig();

    // Optional: accept token from URL once, then scrub it from the address bar.
    // Enables local wrapper to open UI already authenticated.
    try {
        const url = new URL(window.location.href);
        const urlToken = url.searchParams.get('token');
        if (urlToken) {
            document.getElementById('authToken').value = urlToken;
            setToken(urlToken);
            url.searchParams.delete('token');
            window.history.replaceState({}, document.title, url.pathname + url.search);
        }
    } catch (e) {
        /* non-fatal */
    }

    // Restore token
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (savedToken) {
        document.getElementById('authToken').value = savedToken;
    }

    // Listen for token changes
    document.getElementById('authToken').addEventListener('input', (e) => {
        setToken(e.target.value);
        // Retry loading data
        loadArtifacts();
        fetchHealth().then(hub => {
            if (hub) fetchRepos(hub);
        });
    });

    // Also listen for manual hub changes (blur)
    document.getElementById('hubPath').addEventListener('blur', (e) => {
        fetchRepos(e.target.value);
    });

    const hub = await fetchHealth();
    if (hub) {
        // If persisted hub is different from server hub, use persisted if available
        const persisted = document.getElementById('hubPath').value;
        fetchRepos(persisted || hub);
        loadArtifacts();
    } else {
        // Try fetch repos with whatever we have
        const persisted = document.getElementById('hubPath').value;
        if(persisted) fetchRepos(persisted);
        loadArtifacts();
    }

    // Load Atlas artifacts too if tab is visible? Or just always.
    // loadAtlasArtifacts();

    document.getElementById('jobForm').addEventListener('submit', startJob);
    document.getElementById('atlasForm').addEventListener('submit', startAtlasJob);
});

// --- Tabs ---
function switchTab(tabId) {
    document.querySelectorAll('.layout-view').forEach(el => el.classList.add('hidden'));
    document.getElementById(`layout-${tabId}`).classList.remove('hidden');

    // Toggle active state on buttons
    document.getElementById('tab-job').className = tabId === 'job'
        ? "px-3 py-1 rounded bg-blue-600 text-white font-bold text-sm"
        : "px-3 py-1 rounded bg-gray-700 text-gray-300 hover:text-white text-sm";

    document.getElementById('tab-atlas').className = tabId === 'atlas'
        ? "px-3 py-1 rounded bg-blue-600 text-white font-bold text-sm"
        : "px-3 py-1 rounded bg-gray-700 text-gray-300 hover:text-white text-sm";

    if (tabId === 'atlas') {
        loadAtlasArtifacts();
    }
}

// --- Atlas Logic ---
async function startAtlasJob(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerText = "Scanning...";

    const rootInput = document.getElementById('atlasRoot');
    const rootPath = rootInput.value;
    const rootToken = rootInput.dataset.token; // Use token if available from picker

    // Save Atlas Config (path only for display restoration)
    const config = {
        root: rootPath,
        depth: document.getElementById('atlasDepth').value,
        limit: document.getElementById('atlasLimit').value,
        excludes: document.getElementById('atlasExcludes').value
    };
    localStorage.setItem(ATLAS_CONFIG_KEY, JSON.stringify(config));

    const payload = {
        // Prefer token for canonical CodeQL-safe request
        root_token: rootToken || null,
        // Fallback: if no token (manual entry?), try sending root_id if it matches known IDs.
        // If it's a raw path manually typed, the backend will reject it (Hard Cut).
        // The user must use the picker or type a valid root_id ("hub").
        root_id: (['hub', 'merges', 'system'].includes(rootPath)) ? rootPath : null,

        max_depth: parseInt(config.depth),
        max_entries: parseInt(config.limit),
        exclude_globs: config.excludes.split(',').map(s => s.trim())
    };

    try {
        const res = await apiFetch(`${API_BASE}/atlas`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Atlas scan failed: " + res.statusText);

        const art = await res.json();
        alert(`Atlas scan started/completed: ${art.id}`);
        loadAtlasArtifacts();

    } catch (e) {
        alert(e.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "Create Atlas";
    }
}

async function loadAtlasArtifacts() {
    const list = document.getElementById('atlasList');
    list.innerHTML = '<div class="text-gray-500 italic">Loading...</div>';

    try {
        // We only have 'latest' endpoint for now or we could list all files in merges dir via fs list?
        // But app.py has /api/atlas/latest.
        // Let's use /api/atlas/latest to show the current map.
        // Or if we want a list, we need an endpoint.
        // The instruction B3 said: GET /api/atlas/latest.
        // But UI shows "Atlas Results".

        const res = await apiFetch(`${API_BASE}/atlas/latest`);
        if (res.status === 404) {
             list.innerHTML = '<div class="text-gray-500 italic">No atlas artifacts found.</div>';
             return;
        }
        if (!res.ok) throw new Error("Failed to load atlas");

        const art = await res.json();

        list.innerHTML = '';

        const div = document.createElement('div');
        div.className = "bg-gray-900 p-2 rounded border border-gray-700 flex flex-col";

        const date = new Date(art.created_at).toLocaleString();

        // Show Stats if available
        let statsHtml = '';
        if (art.stats && art.stats.total_files) {
            const mb = (art.stats.total_bytes / (1024*1024)).toFixed(2);
            statsHtml = `
                <div class="mt-2 text-xs grid grid-cols-2 gap-2 text-gray-400">
                    <div>Files: <span class="text-white">${art.stats.total_files}</span></div>
                    <div>Dirs: <span class="text-white">${art.stats.total_dirs}</span></div>
                    <div>Size: <span class="text-white">${mb} MB</span></div>
                    <div>Duration: <span class="text-white">${art.stats.duration_seconds.toFixed(2)}s</span></div>
                </div>
            `;
        }

        div.innerHTML = `
            <div class="flex justify-between items-start">
                <span class="font-bold text-green-400">${art.id}</span>
                <span class="text-xs text-gray-500">${date}</span>
            </div>
            <div class="text-xs text-gray-400">Root: ${art.root_scanned}</div>
            ${statsHtml}
            <div class="flex flex-wrap gap-2 text-xs mt-3 border-t border-gray-800 pt-2">
                 <button data-dl="${API_BASE}/atlas/${art.id}/download?key=json" data-name="${art.paths.json}" class="bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded text-green-400">Download JSON</button>
                 <button data-dl="${API_BASE}/atlas/${art.id}/download?key=md" data-name="${art.paths.md}" class="bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded text-blue-400">Download Report</button>
            </div>
        `;
        list.appendChild(div);

        // Wire buttons
        div.querySelectorAll('button[data-dl]').forEach(btn => {
            btn.addEventListener('click', () => {
                downloadWithAuth(btn.getAttribute('data-dl'), btn.getAttribute('data-name'));
            });
        });

    } catch (e) {
        list.innerHTML = `<div class="text-gray-500 italic">Error: ${e.message}</div>`;
    }
}

async function startExport() {
    if (!confirm("Prepare export for webmaschine? This will overwrite files in exports/webmaschine.")) return;

    try {
        const res = await apiFetch(`${API_BASE}/export/webmaschine`, { method: 'POST' });
        if (!res.ok) throw new Error("Export failed");
        const data = await res.json();
        alert(`Export successful!\nPath: ${data.path}`);
    } catch (e) {
        alert(e.message);
    }
}

// Secure download via blob
async function downloadWithAuth(url, name) {
    try {
        const res = await apiFetch(url);

        if (!res.ok) {
            alert("Download failed: " + res.statusText);
            return;
        }

        const blob = await res.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;

        // Try to get filename from header
        // For blob downloads, the name passed in is usually better if available
        // But we can check Content-Disposition if needed.

        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);

    } catch (e) {
        alert("Download error: " + e.message);
    }
}
