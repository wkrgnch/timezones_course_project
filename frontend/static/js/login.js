async function api(path, { method = "GET", body = null, token = null } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`/api/v1${path}`, {
        method,
        headers,
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
    const url = new URL(window.location.href);
    const roleParam = url.searchParams.get("role");
    if (roleParam === "teacher" || roleParam === "student") {
        document.getElementById("role").value = roleParam;
    }

    document.getElementById("loginForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        setStatus("Вхожу…");

        const selectedRole = document.getElementById("role").value;
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        try {
        const loginRes = await api("/auth/login", {
            method: "POST",
            body: { email, password },
        });

        const token = loginRes.access_token;

        // Проверяем роль пользователя по me
        const me = await api("/auth/me", { token });

        const realRole = me.user.role; // teacher  student
        if (realRole !== selectedRole) {
            setStatus(`Ошибка: вы вошли как "${realRole}", а выбрали "${selectedRole}". Выберите правильную роль.`);
            return;
        }

        localStorage.setItem("access_token", token);
        localStorage.setItem("user_full_name", me.user.full_name);

        window.location.href = realRole === "teacher" ? "/ui/teacher.html" : "/ui/student.html";
        } catch (err) {
        setStatus(`Ошибка: ${err.message}`);
        }
    });
});
