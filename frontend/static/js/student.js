function token() {
    return localStorage.getItem("access_token");
}

async function api(path, { method = "GET", body = null } = {}) {
    const t = token();
    const headers = { "Content-Type": "application/json" };
    if (t) headers["Authorization"] = `Bearer ${t}`;

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
    const el = document.getElementById("statusLine");
    if (el) el.textContent = text || "";
}

function showPick(variants) {
    const wrap = document.getElementById("tzPickWrap");
    const select = document.getElementById("tzPick");
    if (!wrap || !select) return;

    select.innerHTML = "";

    variants.forEach((it, idx) => {
        const opt = document.createElement("option");
        opt.value = String(idx);
        opt.textContent = it.label
        ? `${it.region} — ${it.label}`
        : `${it.region} (МСК ${it.msk_offset_hours >= 0 ? "+" : ""}${it.msk_offset_hours})`;
        select.appendChild(opt);
    });

    wrap.classList.remove("d-none");
}

function hidePick() {
    const wrap = document.getElementById("tzPickWrap");
    if (wrap) wrap.classList.add("d-none");
}

document.addEventListener("DOMContentLoaded", async () => {
    if (!token()) {
        window.location.href = "/ui/login.html?role=student";
        return;
    }

    const btnJoin = document.getElementById("btnJoin");
    const joinCodeEl = document.getElementById("joinCode");
    const regionEl = document.getElementById("regionInput");
    const fiasEl = document.getElementById("fiasCodeInput"); 

    let cachedVariants = [];

    btnJoin?.addEventListener("click", async () => {
        try {
        const joinCode = joinCodeEl?.value?.trim() || "";
        const regionRaw = regionEl?.value?.trim() || "";

        if (!joinCode) {
            setStatus("Введи код подключения.");
            return;
        }

        // Если несколько вариантов - берём выбранный и записываем
        const pickWrap = document.getElementById("tzPickWrap");
        const pickSelect = document.getElementById("tzPick");
        const pickVisible = pickWrap && !pickWrap.classList.contains("d-none");

        if (pickVisible && cachedVariants.length && pickSelect) {
            const idx = Number(pickSelect.value);
            const it = cachedVariants[idx];

            setStatus("Записываю с выбранным вариантом…");
            await api("/groups/join", {
            method: "POST",
            body: {
                join_code: joinCode,
                region: it.region,
                msk_offset_hours: it.msk_offset_hours,
            },
            });

            if (fiasEl) fiasEl.value = it.fias_code || "";
            hidePick();
            setStatus("Готово. Ты записан(а) в очередь с учётом часового пояса.");
            return;
        }

        hidePick();
        cachedVariants = [];

        // Если регион не указан - общая очередь
        if (!regionRaw) {
            setStatus("Записываю в общую очередь…");
            await api("/groups/join", { method: "POST", body: { join_code: joinCode } });
            setStatus("Готово. Ты записан(а) в общую очередь.");
            return;
        }

        // Регион указан - resolve
        setStatus("Ищу регион в датасете…");
        const res = await api(`/timezones/resolve?region=${encodeURIComponent(regionRaw)}&limit=20`);
        const variants = res.variants || [];

        if (variants.length === 0) {
            setStatus("Регион не найден. Удали регион и запишись в общую очередь, либо введи по-другому.");
            return;
        }

        // Если несколько - показываем выбор
        if (res.needs_choice || variants.length > 1) {
            cachedVariants = variants;
            showPick(variants);
            setStatus("Нашлось несколько вариантов. Выбери и нажми «Записаться» ещё раз.");
            return;
        }

        // Один вариант - сразу записываем
        const it = variants[0];

        setStatus("Записываю с учётом часового пояса…");
        await api("/groups/join", {
            method: "POST",
            body: {
            join_code: joinCode,
            region: it.region,
            msk_offset_hours: it.msk_offset_hours,
            },
        });

        if (regionEl) regionEl.value = it.region; // нормализуем название
        if (fiasEl) fiasEl.value = it.fias_code || "";

        setStatus("Готово. Ты записан(а) в очередь с учётом часового пояса.");
        } catch (e) {
        setStatus(`Ошибка: ${e.message}`);
        }
    });
});
