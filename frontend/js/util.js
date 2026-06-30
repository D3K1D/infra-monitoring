// Shared helpers used by every dashboard page.

// Escape user/agent-supplied text before putting it into innerHTML so a value
// like a hostname can never inject markup.
function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function formatTimestamp(value) {
    if (!value) return "never";
    return new Date(value).toLocaleString();
}
