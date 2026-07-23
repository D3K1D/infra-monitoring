// Alerts page: list alerts, filter by status, and acknowledge active ones.

const REFRESH_INTERVAL_MS = 10000;
const REPEAT_GROUP_WINDOW_MS = 10 * 60 * 1000;

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

function alertGroupKey(alert) {
    const metric = alert.trigger_reason.split(/[\s:]/, 1)[0].toLowerCase();
    const condition = alert.cleared_at ? "recovered" : "ongoing";
    return `${alert.node_id}|${metric}|${alert.severity}|${condition}`;
}

// The API keeps every historical episode. For display, nearby recovered
// repeats of the same condition are summarized as one flapping incident.
function groupRepeatedAlerts(alerts) {
    const groups = [];
    const latestGroupByKey = new Map();

    for (const alert of alerts) {
        const key = alertGroupKey(alert);
        const createdAt = new Date(alert.created_at).getTime();
        const previousGroup = latestGroupByKey.get(key);
        const closeToPrevious =
            previousGroup
            && Number.isFinite(createdAt)
            && Number.isFinite(previousGroup.oldestCreatedAt)
            && previousGroup.oldestCreatedAt - createdAt <= REPEAT_GROUP_WINDOW_MS;

        if (closeToPrevious) {
            previousGroup.alerts.push(alert);
            previousGroup.oldestCreatedAt = createdAt;
        } else {
            const group = {
                alerts: [alert],
                newest: alert,
                oldestCreatedAt: createdAt,
            };
            groups.push(group);
            latestGroupByKey.set(key, group);
        }
    }
    return groups;
}

function renderRows(alerts) {
    const tbody = document.getElementById("alert-rows");
    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="muted">No alerts to show.</td></tr>';
        return;
    }
    tbody.innerHTML = groupRepeatedAlerts(alerts)
        .map((group) => {
            const alert = group.newest;
            const activeIds = group.alerts
                .filter((item) => item.status === "active")
                .map((item) => item.id);
            const groupStatus = activeIds.length > 0 ? "active" : "acknowledged";
            const action =
                activeIds.length > 0
                    ? `<button data-alert-ids="${activeIds.join(",")}">` +
                      `${activeIds.length > 1 ? "Acknowledge all" : "Acknowledge"}</button>`
                    : "—";
            return `
        <tr>
            <td>${severityBadge(alert.severity)}</td>
            <td>${escapeHtml(alert.hostname)}</td>
            <td>${escapeHtml(alert.trigger_reason)}</td>
            <td>${group.alerts.length}</td>
            <td>${conditionBadge(alert.cleared_at)}</td>
            <td>${statusBadge(groupStatus)}</td>
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

// One listener handles individual alerts and grouped recovered repeats.
document.getElementById("alert-rows").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-alert-ids]");
    if (!button) return;
    button.disabled = true;
    try {
        const alertIds = button.dataset.alertIds.split(",");
        await Promise.all(alertIds.map((alertId) => acknowledgeAlert(alertId)));
        await refresh();
    } catch (err) {
        button.disabled = false;
        console.error(err);
    }
});

document.getElementById("status-filter").addEventListener("change", refresh);

refresh();
setInterval(refresh, REFRESH_INTERVAL_MS);
