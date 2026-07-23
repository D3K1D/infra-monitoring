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
    const details = escapeHtml(reasons.join("\n"));
    const accessibleDetails = escapeHtml(`Warning. ${reasons.join(" ")}`);

    return `
        <span class="badge warning status-tooltip" tabindex="0"
              aria-describedby="warning-status-tooltip"
              aria-label="${accessibleDetails}"
              data-warning-details="${details}">
            warning
        </span>`;
}

const warningTooltip = document.getElementById("warning-status-tooltip");
let activeWarningBadge = null;

function positionWarningTooltip(badge) {
    const gap = 5;
    const margin = 8;
    const badgeRect = badge.getBoundingClientRect();
    const tooltipRect = warningTooltip.getBoundingClientRect();

    let left = badgeRect.left;
    if (left + tooltipRect.width > window.innerWidth - margin) {
        left = window.innerWidth - tooltipRect.width - margin;
    }
    left = Math.max(margin, left);

    let top = badgeRect.bottom + gap;
    if (top + tooltipRect.height > window.innerHeight - margin) {
        top = badgeRect.top - tooltipRect.height - gap;
    }
    top = Math.max(margin, top);

    warningTooltip.style.left = `${Math.round(left)}px`;
    warningTooltip.style.top = `${Math.round(top)}px`;
}

function showWarningTooltip(badge) {
    const details = badge.dataset.warningDetails;
    if (!details) return;

    activeWarningBadge = badge;
    warningTooltip.textContent = details;
    warningTooltip.hidden = false;
    positionWarningTooltip(badge);
}

function hideWarningTooltip(badge = null) {
    if (badge && activeWarningBadge !== badge) return;
    activeWarningBadge = null;
    warningTooltip.hidden = true;
}

function renderRows(nodes) {
    const tbody = document.getElementById("node-rows");
    hideWarningTooltip();
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

document.addEventListener("mouseover", (event) => {
    const badge = event.target.closest(".status-tooltip");
    if (badge) showWarningTooltip(badge);
});

document.addEventListener("mouseout", (event) => {
    const badge = event.target.closest(".status-tooltip");
    if (badge && !badge.contains(event.relatedTarget)) hideWarningTooltip(badge);
});

document.addEventListener("focusin", (event) => {
    const badge = event.target.closest(".status-tooltip");
    if (badge) showWarningTooltip(badge);
});

document.addEventListener("focusout", (event) => {
    const badge = event.target.closest(".status-tooltip");
    if (badge) hideWarningTooltip(badge);
});

window.addEventListener("resize", () => hideWarningTooltip());
document.addEventListener("scroll", () => hideWarningTooltip(), true);

refresh();
setInterval(refresh, REFRESH_INTERVAL_MS);
