/* Enterprise FinTech Admin UI Client Logic */

const API_BASE = "/api/v1/admin";
let currentToken = localStorage.getItem("admin_token") || "";
let currentUserPage = 1;
let currentLogType = "audit";
let maintenanceState = false;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

function initApp() {
  if (currentToken) {
    verifySession();
  } else {
    showLoginOverlay();
  }

  // Setup Event Listeners
  document.getElementById("login-form").addEventListener("submit", handleLogin);
  document.getElementById("logout-btn").addEventListener("click", handleLogout);
  document.getElementById("refresh-btn").addEventListener("click", refreshCurrentView);

  // Navigation Tabs
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      const viewName = item.getAttribute("data-view");
      switchView(viewName);
    });
  });

  // User Search & Filters
  document.getElementById("user-search-btn").addEventListener("click", () => loadUsers(1));
  document.getElementById("user-prev-btn").addEventListener("click", () => loadUsers(currentUserPage - 1));
  document.getElementById("user-next-btn").addEventListener("click", () => loadUsers(currentUserPage + 1));

  // Log Tabs
  document.querySelectorAll("#log-type-tabs button").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#log-type-tabs button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentLogType = btn.getAttribute("data-logtype");
      loadLogs(currentLogType);
    });
  });

  // Export Buttons
  document.getElementById("export-csv-btn").addEventListener("click", () => exportLogs("csv"));
  document.getElementById("export-json-btn").addEventListener("click", () => exportLogs("json"));

  // Toggle Maintenance Mode
  document.getElementById("toggle-maintenance-btn").addEventListener("click", toggleMaintenance);

  // Modal Close Buttons
  document.querySelectorAll(".close-modal-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById("user-modal").style.display = "none";
    });
  });
}

// --- Auth Handlers ---

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Authentication failed.");

    currentToken = data.access_token;
    localStorage.setItem("admin_token", currentToken);
    
    document.getElementById("login-overlay").style.display = "none";
    document.getElementById("app-root").style.display = "flex";

    updateAdminProfile(data.admin);
    showToast("Authenticated successfully. Welcome!", "success");
    switchView("dashboard");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function verifySession() {
  try {
    const res = await apiFetch("/auth/me");
    document.getElementById("login-overlay").style.display = "none";
    document.getElementById("app-root").style.display = "flex";
    updateAdminProfile(res);
    switchView("dashboard");
  } catch (err) {
    showLoginOverlay();
  }
}

function showLoginOverlay() {
  localStorage.removeItem("admin_token");
  currentToken = "";
  document.getElementById("login-overlay").style.display = "flex";
  document.getElementById("app-root").style.display = "none";
}

function handleLogout() {
  showLoginOverlay();
  showToast("Signed out safely.", "success");
}

function updateAdminProfile(admin) {
  document.getElementById("admin-user-name").innerText = admin.username;
  document.getElementById("admin-user-role").innerText = admin.role.toUpperCase();
  document.getElementById("admin-avatar-initials").innerText = admin.username.substring(0, 2).toUpperCase();
}

// --- API Fetch Helper ---

async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (currentToken) {
    headers["Authorization"] = `Bearer ${currentToken}`;
  }
  headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (response.status === 401) {
    showLoginOverlay();
    throw new Error("Session expired. Please log in again.");
  }
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "API Request Failed.");
  }
  return data;
}

// --- View Router ---

function switchView(viewName) {
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.toggle("active", item.getAttribute("data-view") === viewName);
  });

  document.querySelectorAll(".app-view").forEach(v => v.style.display = "none");
  const activeView = document.getElementById(`view-${viewName}`);
  if (activeView) activeView.style.display = "block";

  const titles = {
    dashboard: "Platform Dashboard & Health Overview",
    users: "User Management & Role Permissions",
    monitoring: "System Infrastructure & Connectivity Monitoring",
    logs: "Logs & Security Audit Center",
    config: "System Configuration & Feature Flags",
    support: "Support Requests & Ticket Management"
  };

  document.getElementById("view-title").innerText = titles[viewName] || "Administration";
  refreshCurrentView();
}

function refreshCurrentView() {
  const activeNavItem = document.querySelector(".nav-item.active");
  const viewName = activeNavItem ? activeNavItem.getAttribute("data-view") : "dashboard";

  if (viewName === "dashboard") loadDashboard();
  else if (viewName === "users") loadUsers(currentUserPage);
  else if (viewName === "monitoring") loadMonitoring();
  else if (viewName === "logs") loadLogs(currentLogType);
  else if (viewName === "config") loadConfig();
  else if (viewName === "support") loadSupport();
}

// --- View 1: Dashboard ---

async function loadDashboard() {
  try {
    const data = await apiFetch("/dashboard/stats");
    
    // Top Stats
    document.getElementById("stat-active-users").innerText = data.metrics.active_users;
    document.getElementById("stat-deriv-accounts").innerText = data.metrics.connected_deriv_accounts;
    document.getElementById("stat-deriv-demo").innerText = data.metrics.deriv_demo_accounts;
    document.getElementById("stat-deriv-real").innerText = data.metrics.deriv_real_accounts;
    document.getElementById("stat-sockets").innerText = data.metrics.active_websocket_connections;
    document.getElementById("stat-api-latency").innerText = `${data.metrics.api_metrics.avg_response_time_ms} ms`;

    // Health Badge
    const badge = document.getElementById("system-health-badge");
    const healthText = document.getElementById("health-text");
    if (data.health_status === "healthy") {
      badge.className = "status-badge";
      healthText.innerText = "System Operational";
    } else {
      badge.className = "status-badge degraded";
      healthText.innerText = "System Degraded";
    }

    // Gauges
    document.getElementById("cpu-text").innerText = `${data.resources.cpu_percent}%`;
    document.getElementById("cpu-bar").style.width = `${data.resources.cpu_percent}%`;

    document.getElementById("mem-text").innerText = `${data.resources.memory_used_gb} GB / ${data.resources.memory_total_gb} GB (${data.resources.memory_percent}%)`;
    document.getElementById("mem-bar").style.width = `${data.resources.memory_percent}%`;

    // Activity Feed
    const tbody = document.getElementById("activity-feed-body");
    tbody.innerHTML = data.recent_activity.map(a => `
      <tr>
        <td><strong>${a.actor}</strong></td>
        <td><span class="badge badge-admin">${a.action}</span></td>
        <td>${a.category}</td>
        <td style="color: var(--text-muted); font-size: 0.78rem;">${new Date(a.timestamp).toLocaleString()}</td>
      </tr>
    `).join("") || "<tr><td colspan='4'>No recent activity logged.</td></tr>";

  } catch (err) {
    showToast(`Dashboard error: ${err.message}`, "error");
  }
}

// --- View 2: User Management ---

async function loadUsers(page = 1) {
  currentUserPage = page;
  const search = document.getElementById("user-search-input").value;
  const status = document.getElementById("user-status-filter").value;

  try {
    let query = `?page=${page}&limit=10`;
    if (search) query += `&search=${encodeURIComponent(search)}`;
    if (status) query += `&status=${encodeURIComponent(status)}`;

    const data = await apiFetch(`/users${query}`);
    const tbody = document.getElementById("users-table-body");

    tbody.innerHTML = data.users.map(u => `
      <tr>
        <td>
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <img src="${u.picture || '/static/uploads/nouser.jpeg'}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" onerror="this.src='/static/uploads/nouser.jpeg'">
            <div>
              <strong>${u.name}</strong>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${u.id.substring(0, 8)}...</div>
            </div>
          </div>
        </td>
        <td>${u.email}</td>
        <td><span class="badge badge-user">${u.role}</span></td>
        <td><span class="badge ${u.status === 'active' ? 'badge-active' : 'badge-suspended'}">${u.status}</span></td>
        <td>${new Date(u.created_at).toLocaleDateString()}</td>
        <td>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-secondary btn-sm" onclick="viewUserDetail('${u.id}')"><i class="fas fa-eye"></i></button>
            <button class="btn ${u.status === 'active' ? 'btn-danger' : 'btn-primary'} btn-sm" onclick="toggleUserStatus('${u.id}', '${u.status}')">
              ${u.status === 'active' ? 'Suspend' : 'Reactivate'}
            </button>
          </div>
        </td>
      </tr>
    `).join("") || "<tr><td colspan='6' style='text-align: center;'>No users found matching query.</td></tr>";

    // Pagination
    document.getElementById("user-pagination-info").innerText = `Page ${data.pagination.page} of ${data.pagination.pages} (${data.pagination.total} Total Users)`;
    document.getElementById("user-prev-btn").disabled = data.pagination.page <= 1;
    document.getElementById("user-next-btn").disabled = data.pagination.page >= data.pagination.pages;

  } catch (err) {
    showToast(`Failed to load users: ${err.message}`, "error");
  }
}

async function viewUserDetail(userId) {
  try {
    const data = await apiFetch(`/users/${userId}`);
    document.getElementById("modal-user-name").innerText = `Profile: ${data.profile.name}`;
    
    const body = document.getElementById("modal-user-body");
    body.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="background: #0F172A; padding: 1rem; border-radius: 6px;">
          <div><strong>Email:</strong> ${data.profile.email}</div>
          <div><strong>Status:</strong> ${data.profile.status} | <strong>Role:</strong> ${data.profile.role}</div>
          <div><strong>Last Login:</strong> ${data.profile.last_login ? new Date(data.profile.last_login).toLocaleString() : 'Never'}</div>
        </div>

        <div style="color: var(--gold-primary); font-size: 0.8rem; border: 1px solid var(--gold-glow); padding: 0.75rem; border-radius: 4px;">
          <i class="fas fa-shield-check"></i> ${data.security_note}
        </div>

        <h4>Connected Deriv Accounts (${data.deriv_accounts.length})</h4>
        <div style="max-height: 120px; overflow-y: auto;">
          ${data.deriv_accounts.map(d => `
            <div style="display:flex; justify-between; padding:0.4rem; border-bottom:1px solid #334155;">
              <span><strong>${d.account_id}</strong> (${d.account_type.toUpperCase()})</span>
              <span style="color:var(--emerald-success);">$${d.balance.toFixed(2)} ${d.currency}</span>
            </div>
          `).join("") || "<p style='color:var(--text-muted);'>No linked Deriv accounts.</p>"}
        </div>
      </div>
    `;

    document.getElementById("user-modal").style.display = "flex";
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function toggleUserStatus(userId, currentStatus) {
  const newStatus = currentStatus === "active" ? "suspended" : "active";
  if (!confirm(`Are you sure you want to change user status to ${newStatus}?`)) return;

  try {
    await apiFetch(`/users/${userId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: newStatus, reason: "Admin UI Status Toggle" })
    });
    showToast(`User status updated to ${newStatus}`, "success");
    loadUsers(currentUserPage);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// --- View 3: System Monitoring ---

async function loadMonitoring() {
  try {
    const data = await apiFetch("/monitoring");
    const tbody = document.getElementById("monitoring-table-body");

    tbody.innerHTML = data.services.map(s => `
      <tr>
        <td><strong>${s.name}</strong></td>
        <td><span class="badge ${s.status === 'healthy' || s.status === 'operational' ? 'badge-active' : 'badge-suspended'}">${s.status}</span></td>
        <td>${s.latency_ms} ms</td>
        <td style="color: var(--text-muted); font-size: 0.82rem;">${s.details}</td>
      </tr>
    `).join("");
  } catch (err) {
    showToast(`Monitoring error: ${err.message}`, "error");
  }
}

// --- View 4: Logs & Audit Center ---

async function loadLogs(type = "audit") {
  try {
    const data = await apiFetch(`/logs?log_type=${type}`);
    const thead = document.getElementById("logs-table-head");
    const tbody = document.getElementById("logs-table-body");

    if (type === "audit" || type === "security") {
      thead.innerHTML = `<tr><th>ID</th><th>Actor</th><th>Action</th><th>Category</th><th>Details</th><th>Timestamp</th></tr>`;
      tbody.innerHTML = data.logs.map(l => `
        <tr>
          <td>#${l.id}</td>
          <td><strong>${l.actor}</strong></td>
          <td><span class="badge badge-admin">${l.action}</span></td>
          <td>${l.category}</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${l.details || 'N/A'}</td>
          <td style="font-size: 0.78rem;">${new Date(l.timestamp).toLocaleString()}</td>
        </tr>
      `).join("") || "<tr><td colspan='6'>No logs available.</td></tr>";
    } else if (type === "auth") {
      thead.innerHTML = `<tr><th>ID</th><th>Username</th><th>Event</th><th>Status</th><th>IP Address</th><th>Timestamp</th></tr>`;
      tbody.innerHTML = data.logs.map(l => `
        <tr>
          <td>#${l.id}</td>
          <td><strong>${l.username}</strong></td>
          <td><span class="badge badge-user">${l.event_type}</span></td>
          <td><span class="badge ${l.status === 'SUCCESS' ? 'badge-active' : 'badge-suspended'}">${l.status}</span></td>
          <td>${l.ip || '127.0.0.1'}</td>
          <td style="font-size: 0.78rem;">${new Date(l.timestamp).toLocaleString()}</td>
        </tr>
      `).join("") || "<tr><td colspan='6'>No auth logs available.</td></tr>";
    } else {
      thead.innerHTML = `<tr><th>ID</th><th>Endpoint</th><th>Method</th><th>Status Code</th><th>Latency</th><th>Timestamp</th></tr>`;
      tbody.innerHTML = data.logs.map(l => `
        <tr>
          <td>#${l.id}</td>
          <td><code>${l.endpoint}</code></td>
          <td><strong>${l.method}</strong></td>
          <td><span class="badge badge-active">${l.status_code}</span></td>
          <td>${l.response_time_ms} ms</td>
          <td style="font-size: 0.78rem;">${new Date(l.timestamp).toLocaleString()}</td>
        </tr>
      `).join("") || "<tr><td colspan='6'>No API metrics available.</td></tr>";
    }

  } catch (err) {
    showToast(`Failed to load logs: ${err.message}`, "error");
  }
}

function exportLogs(format = "csv") {
  window.open(`${API_BASE}/logs/export?log_type=${currentLogType}&format=${format}`, "_blank");
}

// --- View 5: Configuration ---

async function loadConfig() {
  try {
    const data = await apiFetch("/config");

    // Maintenance button
    maintenanceState = data.maintenance_mode;
    const btn = document.getElementById("toggle-maintenance-btn");
    btn.innerText = maintenanceState ? "Toggle Off" : "Toggle On";
    btn.className = maintenanceState ? "btn btn-danger btn-sm" : "btn btn-primary btn-sm";

    // Feature Flags
    const container = document.getElementById("feature-flags-list");
    container.innerHTML = Object.entries(data.feature_flags).map(([flag, details]) => `
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
        <div>
          <strong>${flag}</strong>
          <div style="font-size: 0.78rem; color: var(--text-muted);">${details.description || ''}</div>
        </div>
        <button class="btn ${details.enabled ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="toggleFlag('${flag}', ${!details.enabled})">
          ${details.enabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>
    `).join("");

    // Diagnostics
    document.getElementById("diag-backend").innerText = data.system_configuration.backend_server;
    document.getElementById("diag-frontend").innerText = data.system_configuration.frontend_server;
    document.getElementById("diag-deriv").innerText = data.system_configuration.deriv_ws_url;
    document.getElementById("diag-db").innerText = data.system_configuration.database_driver;
    document.getElementById("diag-jwt").innerText = `${data.system_configuration.jwt_expire_minutes} Minutes`;

  } catch (err) {
    showToast(`Config load error: ${err.message}`, "error");
  }
}

async function toggleMaintenance() {
  try {
    await apiFetch("/config/flags", {
      method: "PUT",
      body: JSON.stringify({ flag_name: "maintenance_mode", is_enabled: !maintenanceState })
    });
    showToast(`Maintenance mode toggled to ${!maintenanceState}`, "success");
    loadConfig();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function toggleFlag(flagName, isEnabled) {
  try {
    await apiFetch("/config/flags", {
      method: "PUT",
      body: JSON.stringify({ flag_name: flagName, is_enabled: isEnabled })
    });
    showToast(`Feature flag ${flagName} updated`, "success");
    loadConfig();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// --- View 6: Support Center ---

async function loadSupport() {
  try {
    const data = await apiFetch("/support/tickets");
    const tbody = document.getElementById("tickets-table-body");

    tbody.innerHTML = data.tickets.map(t => `
      <tr>
        <td><strong>${t.ticket_no}</strong></td>
        <td>${t.user_email}</td>
        <td>${t.subject}</td>
        <td>${t.category}</td>
        <td><span class="badge badge-admin">${t.priority}</span></td>
        <td><span class="badge ${t.status === 'OPEN' ? 'badge-active' : 'badge-user'}">${t.status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="showTicketNotes('${t.id}', '${t.ticket_no}')">View Notes (${t.notes.length})</button>
        </td>
      </tr>
    `).join("") || "<tr><td colspan='7' style='text-align: center;'>No support tickets found.</td></tr>";

  } catch (err) {
    showToast(`Support load error: ${err.message}`, "error");
  }
}

function showTicketNotes(ticketId, ticketNo) {
  const noteText = prompt(`Add internal note for ticket ${ticketNo}:`);
  if (!noteText) return;

  apiFetch(`/support/tickets/${ticketId}/notes`, {
    method: "POST",
    body: JSON.stringify({ note_text: noteText })
  }).then(() => {
    showToast("Internal note attached.", "success");
    loadSupport();
  }).catch(err => showToast(err.message, "error"));
}

// --- Toast Utilities ---

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i> <span>${message}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}
