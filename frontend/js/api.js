// Central place for backend calls so the base URL is defined once.
// The dashboard is served by FastAPI itself, so a relative path works from
// any device: same origin, no hostname or port to configure.
const API_BASE = "/api";

// Every call goes through apiFetch so an expired or missing session is
// handled in one place: a 401 sends the user to the login page. The login
// page is exempt so a wrong password doesn't cause a redirect loop.
async function apiFetch(path, options) {
    const response = await fetch(`${API_BASE}${path}`, options);
    const onLoginPage = window.location.pathname.endsWith("login.html");
    if (response.status === 401 && !onLoginPage) {
        window.location.href = "login.html";
        throw new Error("Not logged in");
    }
    return response;
}

// Pull a readable message out of an error response. FastAPI puts plain
// errors in `detail` as a string, but validation errors arrive as a list.
async function errorMessage(response, fallback) {
    const body = await response.json().catch(() => ({}));
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
    return fallback;
}

// ----- Auth -----

async function loginUser(username, password) {
    const response = await apiFetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
        throw new Error(await errorMessage(response, `Login failed: ${response.status}`));
    }
    return response.json();
}

async function registerUser(username, password) {
    const response = await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
        throw new Error(await errorMessage(response, `Registration failed: ${response.status}`));
    }
    return response.json();
}

async function logoutUser() {
    await apiFetch("/auth/logout", { method: "POST" });
}

async function fetchCurrentUser() {
    const response = await apiFetch("/auth/me");
    if (!response.ok) {
        throw new Error(`Failed to load current user: ${response.status}`);
    }
    return response.json();
}

// ----- Dashboard data -----

async function fetchNodes() {
    const response = await apiFetch("/nodes");
    if (!response.ok) {
        throw new Error(`Failed to load nodes: ${response.status}`);
    }
    return response.json();
}

async function fetchNode(nodeId) {
    const response = await apiFetch(`/nodes/${nodeId}`);
    if (!response.ok) {
        throw new Error(`Failed to load node: ${response.status}`);
    }
    return response.json();
}

async function fetchNodeMetrics(nodeId, minutes) {
    const response = await apiFetch(`/nodes/${nodeId}/metrics?minutes=${minutes}`);
    if (!response.ok) {
        throw new Error(`Failed to load metric history: ${response.status}`);
    }
    return response.json();
}

async function fetchSummary(minutes) {
    const response = await apiFetch(`/summary?minutes=${minutes}`);
    if (!response.ok) {
        throw new Error(`Failed to load summary: ${response.status}`);
    }
    return response.json();
}

async function fetchAlerts(status) {
    const path = status ? `/alerts?status=${status}` : "/alerts";
    const response = await apiFetch(path);
    if (!response.ok) {
        throw new Error(`Failed to load alerts: ${response.status}`);
    }
    return response.json();
}

async function acknowledgeAlert(alertId) {
    const response = await apiFetch(`/alerts/${alertId}/acknowledge`, {
        method: "POST",
    });
    if (!response.ok) {
        throw new Error(`Failed to acknowledge alert: ${response.status}`);
    }
    return response.json();
}

async function fetchThresholds() {
    const response = await apiFetch("/thresholds");
    if (!response.ok) {
        throw new Error(`Failed to load thresholds: ${response.status}`);
    }
    return response.json();
}

async function updateThreshold(metricType, warningValue, criticalValue) {
    const response = await apiFetch(`/thresholds/${metricType}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ warning_value: warningValue, critical_value: criticalValue }),
    });
    if (!response.ok) {
        throw new Error(await errorMessage(response, `Failed to update threshold: ${response.status}`));
    }
    return response.json();
}
