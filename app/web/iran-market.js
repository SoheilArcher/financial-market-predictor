let lastIranMarket = null;

function normalizeCountry(country) {
  return (country || "").trim().toLowerCase();
}

function isIranUser() {
  const country = normalizeCountry(state.user?.country);
  return ["ir", "iran", "iran, islamic republic of", "ایران"].includes(country);
}

function formatIranNumber(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toLocaleString("fa-IR");
}

function formatIranPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  return `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
}

function iranBadge(value) {
  return `<span class="badge ${String(value || "").toLowerCase()}">${value || "-"}</span>`;
}

function ensureIranMarketPanel() {
  if (document.getElementById("iranMarketPanel")) return;
  const reportPanel = document.getElementById("reportForm")?.closest(".panel");
  if (!reportPanel) return;
  const panel = document.createElement("section");
  panel.id = "iranMarketPanel";
  panel.className = "panel hidden dashboardBlock";
  panel.dataset.blockId = "iran-market";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>بازار بورس ایران</h2>
        <p class="hint">تابلوی نمادها، صف خرید/فروش و تحلیل اولیه بر اساس داده TSETMC</p>
      </div>
      <button id="loadIranMarketBtn" class="primary" type="button">دریافت بازار ایران</button>
    </div>
    <form id="iranMarketForm" class="iranMarketTools">
      <label>
        نمادها
        <input id="iranMarketSymbols" value="خودرو,فولاد,شتران,شستا,وبملت,فملی,اهرم,طلا" />
      </label>
      <label>
        جست‌وجوی نماد
        <input id="iranSymbolSearch" placeholder="مثلاً شتران یا فولاد" autocomplete="off" />
      </label>
    </form>
    <div id="iranSymbolSuggestions" class="symbolSuggestions hidden"></div>
    <div id="iranMarketBox" class="empty">اگر کشور حساب شما ایران باشد، گزارش بازار ایران اینجا نمایش داده می‌شود.</div>
  `;
  reportPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadIranMarketBtn").addEventListener("click", loadIranMarket);
  document.getElementById("iranMarketForm").addEventListener("submit", (event) => {
    event.preventDefault();
    loadIranMarket();
  });
  document.getElementById("iranSymbolSearch").addEventListener("input", searchIranSymbols);
}

function renderIranMiniList(title, items) {
  const rows = (items || []).map((item) => `
    <tr>
      <td>${item.symbol}</td>
      <td>${formatIranNumber(item.last_price)}</td>
      <td class="${Number(item.last_change_percent || 0) >= 0 ? "positive" : "negative"}">${formatIranPercent(item.last_change_percent)}</td>
      <td>${formatIranNumber(item.trade_value)}</td>
    </tr>
  `).join("");
  return `
    <div class="iranMiniTable">
      <h3>${title}</h3>
      <table>
        <thead><tr><th>نماد</th><th>آخرین</th><th>درصد</th><th>ارزش</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='4'>داده‌ای نیست</td></tr>"}</tbody>
      </table>
    </div>
  `;
}

function renderIranMarket(data) {
  lastIranMarket = data;
  const rows = (data.symbols || []).map((item) => `
    <tr>
      <td><b>${item.symbol}</b><small>${item.name || ""}</small></td>
      <td>${formatIranNumber(item.last_price)}</td>
      <td class="${Number(item.last_change_percent || 0) >= 0 ? "positive" : "negative"}">${formatIranPercent(item.last_change_percent)}</td>
      <td>${formatIranNumber(item.close_price)}</td>
      <td>${formatIranNumber(item.trade_volume)}</td>
      <td>${formatIranNumber(item.trade_value)}</td>
      <td>${item.best_bid_price ? `${formatIranNumber(item.best_bid_price)} / ${formatIranNumber(item.best_bid_volume)}` : "-"}</td>
      <td>${item.best_ask_price ? `${formatIranNumber(item.best_ask_price)} / ${formatIranNumber(item.best_ask_volume)}` : "-"}</td>
      <td>${iranBadge(item.signal)}</td>
      <td>${item.confidence ?? "-"}</td>
      <td>${item.reason_fa || "-"}</td>
    </tr>
  `).join("");
  const box = document.getElementById("iranMarketBox");
  box.className = "reportBox";
  box.innerHTML = `
    <div class="iranSummary">
      <div><span>تعداد نمادهای بررسی‌شده</span><b>${data.count || 0}</b></div>
      <div><span>منبع</span><b>${data.source || "-"}</b></div>
      <div><span>خلاصه</span><b>${data.summary_fa || "-"}</b></div>
    </div>
    <div class="tableWrap iranMainTable">
      <table>
        <thead>
          <tr>
            <th>نماد</th><th>آخرین</th><th>تغییر</th><th>پایانی</th><th>حجم</th><th>ارزش</th>
            <th>بهترین خرید</th><th>بهترین فروش</th><th>سیگنال</th><th>اعتماد</th><th>دلیل</th>
          </tr>
        </thead>
        <tbody>${rows || "<tr><td colspan='11'>نمادی پیدا نشد یا داده در دسترس نیست.</td></tr>"}</tbody>
      </table>
    </div>
    <div class="iranMarketGrid">
      ${renderIranMiniList("بیشترین رشد", data.gainers)}
      ${renderIranMiniList("بیشترین افت", data.losers)}
      ${renderIranMiniList("بیشترین ارزش معاملات", data.value_leaders)}
    </div>
  `;
}

async function loadIranMarket() {
  const box = document.getElementById("iranMarketBox");
  try {
    const symbols = document.getElementById("iranMarketSymbols").value.trim();
    const query = new URLSearchParams({ symbols, limit: "12" }).toString();
    box.className = "empty";
    box.textContent = "در حال دریافت داده بازار ایران...";
    const data = await api(`/iran-market/overview?${query}`);
    renderIranMarket(data);
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

async function searchIranSymbols() {
  const query = document.getElementById("iranSymbolSearch").value.trim();
  const box = document.getElementById("iranSymbolSuggestions");
  if (query.length < 2) {
    box.classList.add("hidden");
    box.innerHTML = "";
    return;
  }
  try {
    const data = await api(`/iran-market/search?q=${encodeURIComponent(query)}&limit=8`);
    const rows = (data.items || []).map((item) => `
      <button type="button" data-symbol="${item.symbol}">
        <b>${item.symbol}</b>
        <span>${item.name || item.industry || ""}</span>
      </button>
    `).join("");
    box.innerHTML = rows || "<div class='empty'>نمادی پیدا نشد.</div>";
    box.classList.remove("hidden");
    box.querySelectorAll("button[data-symbol]").forEach((button) => {
      button.addEventListener("click", () => {
        const input = document.getElementById("iranMarketSymbols");
        const current = input.value.split(",").map((item) => item.trim()).filter(Boolean);
        if (!current.includes(button.dataset.symbol)) current.unshift(button.dataset.symbol);
        input.value = current.slice(0, 12).join(",");
        box.classList.add("hidden");
        loadIranMarket();
      });
    });
  } catch (error) {
    box.innerHTML = `<div class="empty">${error.message}</div>`;
    box.classList.remove("hidden");
  }
}

function renderIranMarketAccess() {
  ensureIranMarketPanel();
  const panel = document.getElementById("iranMarketPanel");
  if (!panel) return;
  const visible = Boolean(state.token && state.user && isIranUser());
  panel.classList.toggle("hidden", !visible);
  if (visible && !lastIranMarket) loadIranMarket();
}

const originalRenderSessionForIran = renderSession;
renderSession = function patchedRenderSession() {
  originalRenderSessionForIran();
  renderIranMarketAccess();
};

ensureIranMarketPanel();
renderIranMarketAccess();
