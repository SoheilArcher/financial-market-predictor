function normalizeCountry(country) {
  return (country || "").trim().toLowerCase();
}

function isIranUser() {
  const country = normalizeCountry(state.user?.country);
  return ["ir", "iran", "iran, islamic republic of", "ایران"].includes(country);
}

function ensureIranMarketPanel() {
  if (document.getElementById("iranMarketPanel")) return;
  const reportPanel = document.getElementById("reportForm")?.closest(".panel");
  if (!reportPanel) return;
  const panel = document.createElement("section");
  panel.id = "iranMarketPanel";
  panel.className = "panel hidden";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>بازار بورس ایران</h2>
        <p class="hint">این بخش برای کاربران ایران فعال می‌شود.</p>
      </div>
      <span class="badge active">IR Market</span>
    </div>
    <div class="iranMarketGrid">
      <div>
        <b>بورس تهران</b>
        <span>اتصال نمادهای TSE در مرحله بعد اضافه می‌شود.</span>
      </div>
      <div>
        <b>فرابورس</b>
        <span>گزارش صنایع، صف خرید/فروش و ارزش معاملات آماده‌سازی می‌شود.</span>
      </div>
      <div>
        <b>صندوق‌ها و طلا</b>
        <span>مسیر تحلیل ETF، طلا و صندوق‌های درآمد ثابت باز می‌شود.</span>
      </div>
    </div>
  `;
  reportPanel.insertAdjacentElement("afterend", panel);
}

function renderIranMarketAccess() {
  ensureIranMarketPanel();
  const panel = document.getElementById("iranMarketPanel");
  if (!panel) return;
  panel.classList.toggle("hidden", !state.token || !state.user || !isIranUser());
}

const originalRenderSessionForIran = renderSession;
renderSession = function patchedRenderSession() {
  originalRenderSessionForIran();
  renderIranMarketAccess();
};

ensureIranMarketPanel();
renderIranMarketAccess();
