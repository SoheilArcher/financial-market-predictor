function ensureNewsPanel() {
  if (document.getElementById("newsPanel")) return;
  const reportPanel = document.getElementById("reportForm")?.closest(".panel");
  if (!reportPanel) return;

  const panel = document.createElement("section");
  panel.id = "newsPanel";
  panel.className = "panel";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>اخبار و اثر روی بازار</h2>
        <p class="hint">خبرها از چند منبع خوانده می‌شوند و کنار تحلیل تکنیکال بررسی می‌شوند.</p>
      </div>
      <button id="loadNewsBtn" class="ghost" type="button">بررسی اخبار</button>
    </div>
    <div class="newsTools">
      <label>
        نمادها
        <input id="newsSymbols" value="BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT" />
      </label>
      <label>
        تعداد خبر
        <input id="newsLimit" type="number" min="5" max="50" value="20" />
      </label>
    </div>
    <div id="newsBox" class="empty">هنوز خبری بررسی نشده است.</div>
  `;
  reportPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadNewsBtn").addEventListener("click", loadNewsReport);
}

function renderNewsReport(report) {
  const summary = report.summary || {};
  const rows = (report.items || []).map((item) => {
    const locale = typeof currentLanguage === "function" && currentLanguage() === "en" ? "en-US" : "fa-IR";
    const published = item.published_at
      ? new Date(item.published_at).toLocaleString(locale)
      : "-";
    const verificationText = item.verification === "cross_source" ? "چند منبع" : "یک منبع";
    return `
      <article class="newsItem">
        <div class="newsItemTop">
          <span class="badge ${String(item.impact || "neutral").toLowerCase()}">${item.impact || "NEUTRAL"}</span>
          <b>${item.title}</b>
        </div>
        <p>${item.description || item.summary_fa || ""}</p>
        <div class="newsMeta">
          <span>${item.source}</span>
          <span>${published}</span>
          <span>${(item.symbols || []).join(", ") || "MARKET"}</span>
          <span>اعتماد: ${item.confidence ?? 0}%</span>
          <span>اعتبار: ${verificationText}</span>
        </div>
        <div class="newsAdvice">${item.summary_fa || ""}</div>
        ${item.url ? `<a href="${item.url}" target="_blank" rel="noreferrer">مشاهده منبع</a>` : ""}
      </article>
    `;
  }).join("");

  document.getElementById("newsBox").className = "reportBox";
  document.getElementById("newsBox").innerHTML = `
    <div class="summaryGrid">
      <div><span>حال‌وهوای خبر</span><b>${summary.mood || "-"}</b></div>
      <div><span>مثبت</span><b>${summary.positive ?? 0}</b></div>
      <div><span>منفی</span><b>${summary.negative ?? 0}</b></div>
      <div><span>خنثی</span><b>${summary.neutral ?? 0}</b></div>
      <div><span>منابع</span><b>${(report.sources || []).length}</b></div>
      <div><span>تعداد خبر</span><b>${(report.items || []).length}</b></div>
    </div>
    <p class="reportSummary">${summary.summary_fa || ""}</p>
    <div class="newsList">${rows || "<div class='empty'>برای این نمادها خبر مرتبط پیدا نشد.</div>"}</div>
  `;
}

async function loadNewsReport() {
  try {
    const symbols = document.getElementById("newsSymbols").value.trim();
    const limit = document.getElementById("newsLimit").value || 20;
    const query = new URLSearchParams({ symbols, limit }).toString();
    document.getElementById("newsBox").className = "empty";
    document.getElementById("newsBox").textContent = "در حال خواندن و بررسی اخبار...";
    const report = await api(`/news/market?${query}`);
    renderNewsReport(report);
  } catch (error) {
    document.getElementById("newsBox").className = "empty";
    document.getElementById("newsBox").textContent = error.message;
  }
}

ensureNewsPanel();
