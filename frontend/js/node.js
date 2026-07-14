// Node detail page: header info plus four metric history charts, refreshed on
// a timer. The node id comes from the query string (node.html?id=3).

const REFRESH_INTERVAL_MS = 10000;

const nodeId = parseInt(new URLSearchParams(window.location.search).get("id"), 10);

const CHART_DEFS = [
    { canvas: "chart-cpu", field: "cpu_percent", color: "#000080" },
    { canvas: "chart-memory", field: "memory_percent", color: "#008000" },
    { canvas: "chart-disk", field: "disk_percent", color: "#9a7000" },
    { canvas: "chart-disk-io", field: "disk_io_percent", color: "#b00000" },
];

const charts = {};

function createCharts() {
    for (const def of CHART_DEFS) {
        charts[def.field] = new Chart(document.getElementById(def.canvas), {
            type: "line",
            data: { labels: [], datasets: [{
                data: [],
                borderColor: def.color,
                borderWidth: 1.5,
                pointRadius: 0,
                fill: false,
            }] },
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { min: 0, max: 100, ticks: { font: { size: 10 } } },
                    x: { ticks: { font: { size: 10 }, maxTicksLimit: 8, maxRotation: 0 } },
                },
            },
        });
    }
}

function renderHeader(node) {
    document.getElementById("node-title").innerHTML =
        `${escapeHtml(node.hostname)} <span class="badge ${escapeHtml(node.status)}">${escapeHtml(node.status)}</span>`;
    const parts = [
        node.ip_address, node.os, node.location,
        `last seen ${formatTimestamp(node.last_seen)}`,
    ].filter(Boolean);
    document.getElementById("node-details").textContent = parts.join("  |  ");
}

function renderCharts(metrics) {
    const labels = metrics.map((m) => new Date(m.recorded_at).toLocaleTimeString());
    for (const def of CHART_DEFS) {
        const chart = charts[def.field];
        chart.data.labels = labels;
        chart.data.datasets[0].data = metrics.map((m) => m[def.field]);
        chart.update();
    }
}

async function refresh() {
    const minutes = document.getElementById("window-select").value;
    try {
        const [node, metrics] = await Promise.all([
            fetchNode(nodeId),
            fetchNodeMetrics(nodeId, minutes),
        ]);
        renderHeader(node);
        renderCharts(metrics);
        document.getElementById("last-updated").textContent =
            `Updated ${new Date().toLocaleTimeString()} — ${metrics.length} readings`;
    } catch (err) {
        document.getElementById("last-updated").textContent = err.message;
        console.error(err);
    }
}

if (Number.isNaN(nodeId)) {
    document.getElementById("node-title").textContent = "No node selected";
    document.getElementById("node-details").innerHTML =
        'Open this page from a hostname link on the <a href="index.html">dashboard</a>.';
} else {
    createCharts();
    document.getElementById("window-select").addEventListener("change", refresh);
    refresh();
    setInterval(refresh, REFRESH_INTERVAL_MS);
}
