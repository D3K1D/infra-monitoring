// Dashboard logic: load nodes, render the table and summary, apply search/filter,
// and refresh automatically on a timer.

const REFRESH_INTERVAL_MS = 10000;
let allNodes = [];
let activeAlertCount = 0;

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

function renderSummary(nodes) {
    const online = nodes.filter((n) => n.status === "online").length;
    const offline = nodes.filter((n) => n.status === "offline").length;
    document.getElementById("count-online").textContent = online;
    document.getElementById("count-offline").textContent = offline;
    document.getElementById("count-alerts").textContent = activeAlertCount;
}

function renderRows(nodes) {
    const tbody = document.getElementById("node-rows");
    if (nodes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="muted">No nodes match.</td></tr>';
        return;
    }
    tbody.innerHTML = nodes
        .map(
            (node) => `
        <tr>
            <td><span class="badge ${escapeHtml(node.status)}">${escapeHtml(node.status)}</span></td>
            <td>${escapeHtml(node.hostname)}</td>
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
    renderSummary(allNodes);
    renderRows(filtered);
}

async function refresh() {
    try {
        const [nodes, activeAlerts] = await Promise.all([
            fetchNodes(),
            fetchAlerts("active"),
        ]);
        allNodes = nodes;
        activeAlertCount = activeAlerts.length;
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

refresh();
setInterval(refresh, REFRESH_INTERVAL_MS);
