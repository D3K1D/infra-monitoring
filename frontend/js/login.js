// Login page: handles the login and registration forms. On success the
// backend sets the HttpOnly session cookie, so there is nothing to store here.

function setMessage(id, text, kind) {
    const el = document.getElementById(id);
    el.textContent = text;
    el.className = kind ? `form-message ${kind}` : "form-message";
}

document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage("login-message", "", "");
    try {
        await loginUser(
            document.getElementById("login-username").value.trim(),
            document.getElementById("login-password").value
        );
        window.location.href = "index.html";
    } catch (err) {
        setMessage("login-message", err.message, "error");
    }
});

document.getElementById("register-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage("register-message", "", "");
    const username = document.getElementById("register-username").value.trim();
    try {
        const user = await registerUser(
            username,
            document.getElementById("register-password").value
        );
        setMessage("register-message", `Account "${user.username}" created — log in above.`, "ok");
        document.getElementById("login-username").value = user.username;
        document.getElementById("login-password").focus();
    } catch (err) {
        setMessage("register-message", err.message, "error");
    }
});
