// Central place for backend calls so the base URL is defined once.
// Built from the page's own hostname so the dashboard works from any device:
// opened on the server it calls the server, opened from the laptop over the
// LAN it calls the server's IP instead of the laptop's localhost.
const API_BASE = `http://${window.location.hostname}:8000/api`;

async function fetchNodes() {
    const response = await fetch(`${API_BASE}/nodes`);
    if (!response.ok) {
        throw new Error(`Failed to load nodes: ${response.status}`);
    }
    return response.json();
}

async function fetchAlerts(status) {
    const url = status ? `${API_BASE}/alerts?status=${status}` : `${API_BASE}/alerts`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to load alerts: ${response.status}`);
    }
    return response.json();
}

async function acknowledgeAlert(alertId) {
    const response = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
        method: "POST",
    });
    if (!response.ok) {
        throw new Error(`Failed to acknowledge alert: ${response.status}`);
    }
    return response.json();
}

async function fetchThresholds() {
    const response = await fetch(`${API_BASE}/thresholds`);
    if (!response.ok) {
        throw new Error(`Failed to load thresholds: ${response.status}`);
    }
    return response.json();
}

async function updateThreshold(metricType, warningValue, criticalValue) {
    const response = await fetch(`${API_BASE}/thresholds/${metricType}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ warning_value: warningValue, critical_value: criticalValue }),
    });
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to update threshold: ${response.status}`);
    }
    return response.json();
}
