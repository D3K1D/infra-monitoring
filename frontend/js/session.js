// Loaded on every logged-in page. Fetches the current user once, fills the
// session area in the menu bar, and wires the logout link. Pages that need
// the user's role (e.g. thresholds) await sessionUserPromise instead of
// calling /auth/me again.

const sessionUserPromise = fetchCurrentUser();

async function initSessionBar() {
    const el = document.getElementById("session-info");
    if (!el) return;
    try {
        const user = await sessionUserPromise;
        el.innerHTML = `
            <span>${escapeHtml(user.username)} (${escapeHtml(user.role)})</span>
            <a href="#" id="logout-link">Log out</a>`;
        document.getElementById("logout-link").addEventListener("click", async (event) => {
            event.preventDefault();
            await logoutUser();
            window.location.href = "login.html";
        });
    } catch (err) {
        // A 401 already redirected to the login page inside apiFetch.
        console.error(err);
    }
}

initSessionBar();
