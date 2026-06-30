// Threshold management page: edit the warning/critical limit for each metric.
// No auto-refresh here so it never overwrites values being typed.

function renderRows(thresholds) {
    const tbody = document.getElementById("threshold-rows");
    tbody.innerHTML = thresholds
        .map(
            (t) => `
        <tr data-metric="${escapeHtml(t.metric_type)}">
            <td>${escapeHtml(t.metric_type)}</td>
            <td><input type="number" class="warning" min="0" max="100" step="1" value="${t.warning_value}"></td>
            <td><input type="number" class="critical" min="0" max="100" step="1" value="${t.critical_value}"></td>
            <td>${escapeHtml(formatTimestamp(t.updated_at))}</td>
            <td>
                <button data-metric="${escapeHtml(t.metric_type)}">Save</button>
                <span class="form-message"></span>
            </td>
        </tr>`
        )
        .join("");
}

async function load() {
    try {
        const thresholds = await fetchThresholds();
        renderRows(thresholds);
        document.getElementById("last-updated").textContent =
            `Loaded ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        document.getElementById("last-updated").textContent = "Backend unreachable";
        console.error(err);
    }
}

async function saveRow(row) {
    const metric = row.dataset.metric;
    const message = row.querySelector(".form-message");
    const warning = parseFloat(row.querySelector(".warning").value);
    const critical = parseFloat(row.querySelector(".critical").value);

    message.className = "form-message";
    if (Number.isNaN(warning) || Number.isNaN(critical)) {
        message.textContent = "Enter numbers for both values.";
        message.classList.add("error");
        return;
    }
    if (warning > critical) {
        message.textContent = "Warning cannot exceed critical.";
        message.classList.add("error");
        return;
    }

    try {
        const updated = await updateThreshold(metric, warning, critical);
        message.textContent = "Saved.";
        message.classList.add("ok");
        // Reflect the server-side updated timestamp.
        row.children[3].textContent = formatTimestamp(updated.updated_at);
    } catch (err) {
        message.textContent = err.message;
        message.classList.add("error");
    }
}

document.getElementById("threshold-rows").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-metric]");
    if (!button) return;
    saveRow(button.closest("tr"));
});

load();
