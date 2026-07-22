// Admin user management: list accounts, change roles, and remove accounts.

let currentUser = null;

function renderRows(users) {
    const tbody = document.getElementById("user-rows");
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="muted">No users found.</td></tr>';
        return;
    }

    tbody.innerHTML = users
        .map((user) => {
            const isCurrentUser = user.id === currentUser.id;
            return `
        <tr data-user-id="${user.id}">
            <td>${escapeHtml(user.username)}${isCurrentUser ? " (you)" : ""}</td>
            <td>
                <select class="role-select">
                    <option value="admin" ${user.role === "admin" ? "selected" : ""}>Admin</option>
                    <option value="technician" ${user.role === "technician" ? "selected" : ""}>Technician</option>
                </select>
            </td>
            <td>${escapeHtml(formatTimestamp(user.created_at))}</td>
            <td>
                <button data-action="save">Save</button>
                <button data-action="delete" ${isCurrentUser ? "disabled" : ""}>Delete</button>
                <span class="form-message"></span>
            </td>
        </tr>`;
        })
        .join("");
}

async function load() {
    try {
        const results = await Promise.all([fetchUsers(), sessionUserPromise]);
        const users = results[0];
        currentUser = results[1];
        renderRows(users);
        document.getElementById("last-updated").textContent =
            `Loaded ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        document.getElementById("user-rows").innerHTML =
            `<tr><td colspan="4" class="muted">${escapeHtml(err.message)}</td></tr>`;
        document.getElementById("last-updated").textContent = "Admin access required";
    }
}

async function saveRole(row) {
    const message = row.querySelector(".form-message");
    message.className = "form-message";
    try {
        const updated = await updateUserRole(
            row.dataset.userId,
            row.querySelector(".role-select").value
        );
        if (updated.id === currentUser.id && updated.role !== "admin") {
            window.location.href = "index.html";
            return;
        }
        message.textContent = "Saved.";
        message.classList.add("ok");
    } catch (err) {
        message.textContent = err.message;
        message.classList.add("error");
    }
}

async function removeUser(row) {
    const message = row.querySelector(".form-message");
    if (!window.confirm("Delete this user account?")) return;
    try {
        await deleteUserAccount(row.dataset.userId);
        await load();
    } catch (err) {
        message.textContent = err.message;
        message.className = "form-message error";
    }
}

document.getElementById("user-rows").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const row = button.closest("tr");
    if (button.dataset.action === "save") saveRole(row);
    if (button.dataset.action === "delete") removeUser(row);
});

load();
