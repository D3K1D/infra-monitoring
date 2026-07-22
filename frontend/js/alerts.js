// Alerts page: list alerts, filter by status, and acknowledge active ones.

const REFRESH_INTERVAL_MS = 10000;

function severityBadge(severity) {
    return `<span class="badge ${escapeHtml(severity)}">${escapeHtml(severity)}</span>`;
}

function statusBadge(status) {
    const label = status === "active" ? "unacknowledged" : status;
    return `<span class="badge ${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

function conditionBadge(clearedAt) {
    const condition = clearedAt ? "recovered" : "ongoing";
    return `<span class="badge ${condition}">${condition}</span>`;
}

function renderRows(alerts) {
    const tbody = document.getElementById("alert-rows");
    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="muted">No alerts to show.</td></tr>';
        return;
    }
    tbody.innerHTML = alerts
        .map((alert) => {
            const action =
                alert.status === "active"
                    ? `<button data-alert-id="${alert.id}">Acknowledge</button>`
                    : "—";
            return `
        <tr>
            <td>${severityBadge(alert.severity)}</td>
            <td>${escapeHtml(alert.hostname)}</td>
            <td>${escapeHtml(alert.trigger_reason)}</td>
            <td>${conditionBadge(alert.cleared_at)}</td>
            <td>${statusBadge(alert.status)}</td>
            <td>${escapeHtml(formatTimestamp(alert.created_at))}</td>
            <td>${action}</td>
        </tr>`;
        })
        .join("");
}

async function refresh() {
    const filter = document.getElementById("status-filter").value;
    try {
        const alerts = await fetchAlerts(filter === "all" ? undefined : filter);
        renderRows(alerts);
        document.getElementById("last-updated").textContent =
            `Updated ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        document.getElementById("last-updated").textContent = "Backend unreachable";
        console.error(err);
    }
}

// One listener for the whole table handles every Acknowledge button.
document.getElementById("alert-rows").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-alert-id]");
    if (!button) return;
    button.disabled = true;
    try {
        await acknowledgeAlert(button.dataset.alertId);
        await refresh();
    } catch (err) {
        button.disabled = false;
        console.error(err);
    }
});

document.getElementById("status-filter").addEventListener("change", refresh);

refresh();
setInterval(refresh, REFRESH_INTERVAL_MS);
