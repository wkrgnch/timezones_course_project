(() => {
    const regionInput = document.getElementById("regionInput");
    const datalist = document.getElementById("regionsDatalist");

    if (!regionInput || !datalist) return;

    let timer = null;

    async function tzSearch(q) {
        const params = new URLSearchParams({ q, limit: "8" });
        const res = await fetch(`/api/v1/timezones/search?${params.toString()}`);
        if (!res.ok) return [];
        return await res.json();
    }

    function render(items) {
        datalist.innerHTML = "";
        for (const it of items) {
        const opt = document.createElement("option");
        opt.value = it.region;
        datalist.appendChild(opt);
        }
    }

    regionInput.addEventListener("input", () => {
        const q = regionInput.value.trim();

        if (timer) clearTimeout(timer);

        timer = setTimeout(async () => {
        if (q.length < 2) {
            render([]);
            return;
        }
        const items = await tzSearch(q);
        render(items);
        }, 250);
    });
})();
