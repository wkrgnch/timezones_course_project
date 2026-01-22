async function tzSearch(query) {
    const url = `/api/v1/timezones/search?q=${encodeURIComponent(query)}&limit=8`;
    const res = await fetch(url);
    if (!res.ok) return [];
    return await res.json();
}

async function tzNow(region) {
    const url = `/api/v1/timezones/now?region=${encodeURIComponent(region)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Region not found");
    return await res.json();
}

function attachAutocomplete(input, onPick) {
    const wrap = document.createElement("div");
    wrap.className = "position-relative";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    const list = document.createElement("div");
    list.className = "list-group position-absolute w-100 shadow";
    list.style.zIndex = "1000";
    list.style.top = "100%";
    list.style.display = "none";
    wrap.appendChild(list);

    let timer = null;

    function hide() {
        list.innerHTML = "";
        list.style.display = "none";
    }

    function show(items) {
        list.innerHTML = "";
        if (!items.length) return hide();

        for (const it of items) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "list-group-item list-group-item-action";
        btn.textContent = it.region;
        btn.addEventListener("click", () => {
            input.value = it.region;
            hide();
            onPick && onPick(it.region);
        });
        list.appendChild(btn);
        }
        list.style.display = "block";
    }

    input.addEventListener("input", () => {
        const q = input.value.trim();
        if (timer) clearTimeout(timer);

        timer = setTimeout(async () => {
        if (q.length < 2) return hide();
        const items = await tzSearch(q);
        show(items);
        }, 250);
    });

    document.addEventListener("click", (e) => {
        if (!wrap.contains(e.target)) hide();
    });
}

window.TZ = { tzNow, tzSearch, attachAutocomplete };
