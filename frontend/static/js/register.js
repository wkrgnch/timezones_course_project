async function api(path, { method = "GET", body = null } = {}) {
    const res = await fetch(`/api/v1${path}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : null,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    return data;
}

function setStatus(text) {
    document.getElementById("status").textContent = text || "";
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("registerForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        setStatus("Регистрирую…");

        const payload = {
        role: document.getElementById("role").value,
        full_name: document.getElementById("full_name").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
        };

        try {
        await api("/auth/register", { method: "POST", body: payload });
        setStatus("Готово. Теперь можно войти.");
        setTimeout(() => (window.location.href = "/ui/login.html"), 800);
        } catch (err) {
        setStatus(`Ошибка: ${err.message}`);
        }
    });
});
