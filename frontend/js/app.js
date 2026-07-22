// Dashboard logic: load nodes, render the table and summary, apply search/filter,
// and refresh automatically on a timer.

const REFRESH_INTERVAL_MS = 10000;
let allNodes = [];
let diskThreshold = { warning_value: 80, critical_value: 90 };

function applyFilters(nodes) {
    const term = document.getElementById("search").value.trim().toLowerCase();
    const statusFilter = document.getElementById("status-filter").value;

    return nodes.filter((node) => {
        const matchesStatus = statusFilter === "all" || node.status === statusFilter;
        const haystack = `${node.hostname} ${node.ip_address || ""}`.toLowerCase();
        const matchesTerm = term === "" || haystack.includes(term);
        return matchesStatus && matchesTerm;
    });
}

function renderSummary(summary) {
    document.getElementById("count-total").textContent = summary.total_nodes;
    document.getElementById("count-online").textContent = summary.online;
    document.getElementById("count-warning").textContent = summary.warning;
    document.getElementById("count-offline").textContent = summary.offline;
    document.getElementById("count-alerts").textContent = summary.active_alerts;
    document.getElementById("alert-breakdown").textContent =
        `${summary.ongoing_alerts} ongoing / ` +
        `${summary.recovered_unacknowledged} recovered`;
    document.getElementById("uptime").textContent =
        summary.uptime_percent === null ? "—" : `${summary.uptime_percent}%`;

    const summaryWindow = document.getElementById("summary-window");
    const selectedLabel = summaryWindow.options[summaryWindow.selectedIndex].text;
    document.getElementById("uptime-label").textContent = `Uptime (${selectedLabel})`;
}

// Sunken progress bar showing how full the node's disk is. Fill and text color
// step green -> amber -> red at the configured disk warning/critical thresholds.
function diskSpaceBar(percent) {
    if (percent === null || percent === undefined) {
        return '<span class="muted">—</span>';
    }
    const level = percent >= diskThreshold.critical_value
        ? "high"
        : percent >= diskThreshold.warning_value ? "mid" : "low";
    const width = Math.min(Math.max(percent, 0), 100);
    return `
        <div class="disk-cell">
            <div class="disk-bar"><div class="disk-fill ${level}" style="width: ${width}%"></div></div>
            <span class="disk-label ${level}">${percent.toFixed(1)}%</span>
        </div>`;
}

function statusBadge(node) {
    const status = escapeHtml(node.status);
    if (node.status !== "warning") {
        return `<span class="badge ${status}">${status}</span>`;
    }

    const reasons = Array.isArray(node.warning_reasons) && node.warning_reasons.length > 0
        ? node.warning_reasons
        : ["One or more current metrics are above the configured threshold."];
    const tooltipId = `warning-details-${node.id}`;
    const details = reasons
        .map((reason) => `<span>${escapeHtml(reason)}</span>`)
        .join("");

    return `
        <span class="badge warning status-tooltip" tabindex="0"
              aria-describedby="${tooltipId}">
            warning
            <span class="status-tooltip-text" id="${tooltipId}" role="tooltip">${details}</span>
        </span>`;
}

function renderRows(nodes) {
    const tbody = document.getElementById("node-rows");
    if (nodes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="muted">No nodes match.</td></tr>';
        return;
    }
    tbody.innerHTML = nodes
        .map(
            (node) => `
        <tr>
            <td>${statusBadge(node)}</td>
            <td>${diskSpaceBar(node.disk_percent)}</td>
            <td><a class="node-link" href="node.html?id=${node.id}">${escapeHtml(node.hostname)}</a></td>
            <td>${escapeHtml(node.ip_address) || "—"}</td>
            <td>${escapeHtml(node.os) || "—"}</td>
            <td>${escapeHtml(node.location) || "—"}</td>
            <td>${escapeHtml(formatTimestamp(node.last_seen))}</td>
        </tr>`
        )
        .join("");
}

function render() {
    const filtered = applyFilters(allNodes);
    renderRows(filtered);
}

async function refresh() {
    try {
        const minutes = parseInt(document.getElementById("summary-window").value, 10);
        const [nodes, summary, thresholds] = await Promise.all([
            fetchNodes(),
            fetchSummary(minutes),
            fetchThresholds(),
        ]);
        allNodes = nodes;
        diskThreshold = thresholds.find((threshold) => threshold.metric_type === "disk")
            || diskThreshold;
        renderSummary(summary);
        render();
        document.getElementById("last-updated").textContent =
            `Updated ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        document.getElementById("last-updated").textContent = "Backend unreachable";
        console.error(err);
    }
}

document.getElementById("search").addEventListener("input", render);
document.getElementById("status-filter").addEventListener("change", render);
document.getElementById("summary-window").addEventListener("change", refresh);

refresh();
setInterval(refresh, REFRESH_INTERVAL_MS);
