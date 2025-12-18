// repoLens UI Logic

const API_BASE = '/api';

// Token handling
const TOKEN_KEY = 'repolens_token';

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
        document.getElementById('hubPath').value = data.hub;
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
        const res = await apiFetch(`${API_BASE}/repos`);
        if (res.status === 401 || res.status === 403) {
             list.innerHTML = '<div class="text-red-400">Access Denied (Check Token)</div>';
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
            div.className = "flex items-center space-x-2";
            div.innerHTML = `
                <input type="checkbox" name="repos" value="${repo}" class="form-checkbox text-blue-500 bg-gray-900 border-gray-700">
                <span>${repo}</span>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        list.innerHTML = '<div class="text-red-500">Error loading repos.</div>';
    }
}

function selectAllRepos() {
    const boxes = document.querySelectorAll('input[name="repos"]');
    const allChecked = Array.from(boxes).every(b => b.checked);
    boxes.forEach(b => b.checked = !allChecked);
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

    const selectedRepos = Array.from(document.querySelectorAll('input[name="repos"]:checked')).map(cb => cb.value);

    // Extensions
    const extRaw = document.getElementById('extFilter').value.trim();
    const extensions = extRaw ? extRaw.split(',').map(s => s.trim()) : null;

    const payload = {
        hub: document.getElementById('hubPath').value,
        repos: selectedRepos.length > 0 ? selectedRepos : null,
        level: document.getElementById('profile').value,
        mode: document.getElementById('mode').value,
        max_bytes: document.getElementById('maxBytes').value,
        split_size: document.getElementById('splitSize').value,
        plan_only: document.getElementById('planOnly').checked,
        code_only: document.getElementById('codeOnly').checked,
        json_sidecar: document.getElementById('jsonSidecar').checked,
        path_filter: document.getElementById('pathFilter').value.trim() || null,
        extensions: extensions,
        extras: document.getElementById('extras').value.trim()
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

    const hub = await fetchHealth();
    if (hub) {
        fetchRepos(hub);
        loadArtifacts();
    }

    document.getElementById('jobForm').addEventListener('submit', startJob);
});

// Secure download via blob
async function downloadArtifact(id, key) {
    try {
        const url = `${API_BASE}/artifacts/${id}/download?key=${key}`;
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
        const contentDisp = res.headers.get('Content-Disposition');
        let filename = `artifact-${id}.${key === 'json' ? 'json' : 'md'}`;
        if (contentDisp && contentDisp.indexOf('filename=') !== -1) {
            filename = contentDisp.split('filename=')[1].replace(/['"]/g, '');
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);

    } catch (e) {
        alert("Download error: " + e.message);
    }
}
