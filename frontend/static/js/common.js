function getToken() {
    return localStorage.getItem("access_token");
}

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_full_name");
    window.location.href = "/ui/";
}

function fillUserName() {
    const name = localStorage.getItem("user_full_name");
    const el = document.getElementById("navUserName");
    if (el) el.textContent = name ? name : "";
}

document.addEventListener("DOMContentLoaded", () => {
    fillUserName();
    const btn = document.getElementById("btnLogout");
    if (btn) btn.addEventListener("click", logout);
});
