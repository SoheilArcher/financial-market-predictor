let lastNewsReport = null;

const newsText = {
  fa: {
    title: "اخبار و اثر روی بازار",
    hint: "خبرها از چند منبع خوانده می‌شوند و کنار تحلیل تکنیکال بررسی می‌شوند.",
    load: "بررسی اخبار",
    symbols: "نمادها",
    limit: "تعداد خبر",
    empty: "هنوز خبری بررسی نشده است.",
    loading: "در حال خواندن و بررسی اخبار...",
    mood: "حال‌وهوای خبر",
    positive: "مثبت",
    negative: "منفی",
    neutral: "خنثی",
    sources: "منابع",
    count: "تعداد خبر",
    confidence: "اعتماد",
    verification: "اعتبار",
    cross: "چند منبع",
    single: "یک منبع",
    sourceLink: "مشاهده منبع",
    noData: "برای این نمادها خبر مرتبط پیدا نشد.",
    newsText: "متن خبر به فارسی",
    marketImpact: "اثر احتمالی روی بازار",
    original: "متن کوتاه اصلی",
  },
  en: {
    title: "News and Market Impact",
    hint: "News is checked from multiple sources and compared with technical analysis.",
    load: "Check News",
    symbols: "Symbols",
    limit: "News Count",
    empty: "No news report yet.",
    loading: "Reading and analyzing news...",
    mood: "News Mood",
    positive: "Positive",
    negative: "Negative",
    neutral: "Neutral",
    sources: "Sources",
    count: "News Count",
    confidence: "Confidence",
    verification: "Verification",
    cross: "Cross-source",
    single: "Single source",
    sourceLink: "Open Source",
    noData: "No related news was found for these symbols.",
    newsText: "News Text",
    marketImpact: "Potential Market Impact",
    original: "Short Original Text",
  },
};

function nt(key) {
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  return newsText[lang]?.[key] || newsText.fa[key] || key;
}

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
  applyNewsLanguage();
}

function applyNewsLanguage() {
  const panel = document.getElementById("newsPanel");
  if (!panel) return;
  panel.querySelector(".panelHeader h2").textContent = nt("title");
  panel.querySelector(".panelHeader .hint").textContent = nt("hint");
  document.getElementById("loadNewsBtn").textContent = nt("load");
  const symbolLabel = panel.querySelector('label:has(#newsSymbols)');
  if (symbolLabel?.firstChild) symbolLabel.firstChild.textContent = `${nt("symbols")}\n`;
  const limitLabel = panel.querySelector('label:has(#newsLimit)');
  if (limitLabel?.firstChild) limitLabel.firstChild.textContent = `${nt("limit")}\n`;
  const box = document.getElementById("newsBox");
  if (box && box.className === "empty" && !lastNewsReport) box.textContent = nt("empty");
  if (lastNewsReport) renderNewsReport(lastNewsReport);
}

function renderNewsReport(report) {
  lastNewsReport = report;
  const summary = report.summary || {};
  const isFa = typeof currentLanguage !== "function" || currentLanguage() === "fa";
  const rows = (report.items || []).map((item) => {
    const locale = typeof currentLanguage === "function" && currentLanguage() === "en" ? "en-US" : "fa-IR";
    const published = item.published_at
      ? new Date(item.published_at).toLocaleString(locale)
      : "-";
    const verificationText = item.verification === "cross_source" ? nt("cross") : nt("single");
    const title = isFa ? (item.title_fa || item.summary_fa || item.title) : item.title;
    const newsText = isFa ? (item.news_text_fa || item.description_fa || item.summary_fa || item.description) : (item.description || item.original_excerpt || item.summary_en || "");
    const impactText = isFa ? (item.description_fa || item.summary_fa || "") : (item.summary_en || item.summary_fa || "");
    return `
      <article class="newsItem">
        <div class="newsItemTop">
          <span class="badge ${String(item.impact || "neutral").toLowerCase()}">${item.impact || "NEUTRAL"}</span>
          <b>${title}</b>
        </div>
        <div class="newsReadable">
          <b>${nt("newsText")}</b>
          <p>${newsText}</p>
        </div>
        <div class="newsAdvice">
          <b>${nt("marketImpact")}</b>
          <p>${impactText}</p>
        </div>
        ${item.original_excerpt ? `<details class="newsOriginal"><summary>${nt("original")}</summary><p>${item.original_excerpt}</p></details>` : ""}
        <div class="newsMeta">
          <span>${item.source}</span>
          <span>${published}</span>
          <span>${(item.symbols || []).join(", ") || "MARKET"}</span>
          <span>${nt("confidence")}: ${item.confidence ?? 0}%</span>
          <span>${nt("verification")}: ${verificationText}</span>
        </div>
        ${item.url ? `<a href="${item.url}" target="_blank" rel="noreferrer">${nt("sourceLink")}</a>` : ""}
      </article>
    `;
  }).join("");

  document.getElementById("newsBox").className = "reportBox";
  document.getElementById("newsBox").innerHTML = `
    <div class="summaryGrid">
      <div><span>${nt("mood")}</span><b>${summary.mood || "-"}</b></div>
      <div><span>${nt("positive")}</span><b>${summary.positive ?? 0}</b></div>
      <div><span>${nt("negative")}</span><b>${summary.negative ?? 0}</b></div>
      <div><span>${nt("neutral")}</span><b>${summary.neutral ?? 0}</b></div>
      <div><span>${nt("sources")}</span><b>${(report.sources || []).length}</b></div>
      <div><span>${nt("count")}</span><b>${(report.items || []).length}</b></div>
    </div>
    <p class="reportSummary">${isFa ? (summary.summary_fa || "") : (summary.summary_en || summary.summary_fa || "")}</p>
    <div class="newsList">${rows || `<div class='empty'>${nt("noData")}</div>`}</div>
  `;
}

async function loadNewsReport() {
  try {
    const symbols = document.getElementById("newsSymbols").value.trim();
    const limit = document.getElementById("newsLimit").value || 20;
    const query = new URLSearchParams({ symbols, limit }).toString();
    document.getElementById("newsBox").className = "empty";
    document.getElementById("newsBox").textContent = nt("loading");
    const report = await api(`/news/market?${query}`);
    renderNewsReport(report);
  } catch (error) {
    document.getElementById("newsBox").className = "empty";
    document.getElementById("newsBox").textContent = error.message;
  }
}

ensureNewsPanel();
window.addEventListener("market-ai-language-change", applyNewsLanguage);
