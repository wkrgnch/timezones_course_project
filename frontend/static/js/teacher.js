let GROUPS = []; 

async function api(path, { method = "GET", body = null } = {}) {
    const token = localStorage.getItem("access_token");
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
    document.getElementById("statusLine").textContent = text || "";
}

function currentGroupId() {
    const v = document.getElementById("groupSelect").value;
    return v ? Number(v) : null;
    }

function updateJoinCodeView(groupId) {
    const el = document.getElementById("joinCodeView");
    const g = GROUPS.find(x => x.id === groupId);
    el.textContent = g ? g.join_code : "-";
}

function renderQueue(queue) {
    const body = document.getElementById("queueBody");
    body.innerHTML = "";

    if (!queue || queue.length === 0) {
        body.innerHTML = `<tr><td colspan="5" class="text-muted">Пока пусто</td></tr>`;
        return;
    }

    queue.forEach((p, idx) => {
        const region = p.region || "—";
        const msk = (p.msk_offset_hours === null || p.msk_offset_hours === undefined) ? "—" : String(p.msk_offset_hours);
        const pr = (p.position === null || p.position === undefined) ? "—" : String(p.position);

        const tr = document.createElement("tr");
        tr.innerHTML = `
        <td class="text-muted">${idx + 1}</td>
        <td>${escapeHtml(p.display_name || "—")}</td>
        <td>${escapeHtml(region)}</td>
        <td>${escapeHtml(msk)}</td>
        <td>${escapeHtml(pr)}</td>
        `;
        body.appendChild(tr);
    });
    }

// защита от HTML в полях
function escapeHtml(v) {
    return String(v)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadMe() {
    const me = await api("/auth/me");
    document.getElementById("me").textContent = `${me.user.full_name} (${me.user.role})`;
    if (me.user.role !== "teacher") throw new Error("Нужна роль teacher");
}

async function loadGroups(selectAfterId = null) {
    GROUPS = await api("/groups/my");

    const sel = document.getElementById("groupSelect");
    sel.innerHTML = "";

    if (GROUPS.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Нет созданных групп";
        sel.appendChild(opt);
        updateJoinCodeView(null);
        renderQueue([]);
        return;
    }

    GROUPS.forEach(g => {
        const opt = document.createElement("option");
        opt.value = g.id;
        opt.textContent = `${g.group_number} (создана)`;
        sel.appendChild(opt);
    });

    if (selectAfterId && GROUPS.some(g => g.id === selectAfterId)) {
        sel.value = String(selectAfterId);
    }

    const gid = currentGroupId();
    updateJoinCodeView(gid);
    await refreshQueue();
    }

async function refreshQueue() {
    const gid = currentGroupId();
    if (!gid) return;

    setStatus("Обновляю очередь…");
    try {
        const res = await api(`/groups/${gid}/queue`);
        renderQueue(res.queue || []);
        setStatus("");
    } catch (e) {
        setStatus(`Ошибка: ${e.message}`);
    }
}

async function createGroup() {
    const num = document.getElementById("groupNumber").value.trim();
    if (!num) {
        setStatus("Введи номер группы.");
        return;
    }

    setStatus("Создаю группу…");
    try {
        const g = await api("/groups", { method: "POST", body: { group_number: num } });
        setStatus(`Группа создана. Код: ${g.join_code}`);
        document.getElementById("groupNumber").value = "";
        await loadGroups(g.id);
    } catch (e) {
        setStatus(`Ошибка: ${e.message}`);
    }
}

async function finishDefense() {
    const gid = currentGroupId();
    if (!gid) return;

    if (!confirm("Очистить очередь этой группы?")) return;

    setStatus("Очищаю очередь…");
    try {
        const res = await api(`/groups/${gid}/finish`, { method: "POST" });
        setStatus(`Готово. Удалено записей: ${res.deleted}`);
        await refreshQueue();
    } catch (e) {
        setStatus(`Ошибка: ${e.message}`);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadMe();
        } catch (e) {
        alert("Нужен вход преподавателя. Сначала авторизуйтесь (токен) и откройте страницу заново.");
        return;
        }

    document.getElementById("btnCreateGroup").addEventListener("click", createGroup);
    document.getElementById("btnRefresh").addEventListener("click", refreshQueue);
    document.getElementById("btnFinish").addEventListener("click", finishDefense);

    document.getElementById("groupSelect").addEventListener("change", async () => {
        updateJoinCodeView(currentGroupId());
        await refreshQueue();
    });

    await loadGroups();
});
