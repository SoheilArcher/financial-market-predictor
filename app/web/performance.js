let lastPerformanceData = null;

const performanceText = {
  fa: {
    title: "ارزیابی عملکرد سیگنال‌ها",
    hint: "سیستم بررسی می‌کند در چند روز اخیر چند تحلیل درست بوده و در ضرر چه باید کرد.",
    load: "بررسی عملکرد",
    days: "چند روز اخیر",
    timeframe: "تایم‌فریم",
    all: "همه",
    empty: "هنوز گزارشی گرفته نشده است.",
    loading: "در حال ارزیابی سیگنال‌ها...",
    total: "کل سیگنال‌ها",
    reviewed: "بررسی‌شده",
    correct: "درست",
    wrong: "غلط",
    neutral: "خنثی",
    pending: "در انتظار",
    accuracy: "دقت",
    range: "بازه",
    symbol: "نماد",
    signal: "سیگنال",
    result: "نتیجه",
    percent: "درصد",
    drawdown: "اگر رفت تو ضرر",
    noData: "داده‌ای نیست",
  },
  en: {
    title: "Signal Performance",
    hint: "The system reviews recent analyses and shows what to do in drawdown.",
    load: "Review Performance",
    days: "Recent Days",
    timeframe: "Timeframe",
    all: "All",
    empty: "No report loaded yet.",
    loading: "Evaluating signals...",
    total: "Total Signals",
    reviewed: "Reviewed",
    correct: "Correct",
    wrong: "Wrong",
    neutral: "Neutral",
    pending: "Pending",
    accuracy: "Accuracy",
    range: "Range",
    symbol: "Symbol",
    signal: "Signal",
    result: "Result",
    percent: "Percent",
    drawdown: "Drawdown Advice",
    noData: "No data",
  },
};

function pt(key) {
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  return performanceText[lang]?.[key] || performanceText.fa[key] || key;
}

function ensurePerformancePanel() {
  if (document.getElementById("performancePanel")) return;
  const reportPanel = document.getElementById("reportForm")?.closest(".panel");
  if (!reportPanel) return;
  const panel = document.createElement("section");
  panel.id = "performancePanel";
  panel.className = "panel";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>ارزیابی عملکرد سیگنال‌ها</h2>
        <p class="hint">سیستم بررسی می‌کند در چند روز اخیر چند تحلیل درست بوده و در ضرر چه باید کرد.</p>
      </div>
      <button id="loadPerformanceBtn" class="ghost" type="button">بررسی عملکرد</button>
    </div>
    <div class="performanceTools">
      <label>
        چند روز اخیر
        <input id="performanceDays" type="number" min="1" max="90" value="7" />
      </label>
      <label>
        تایم‌فریم
        <select id="performanceTimeframe">
          <option value="">همه</option>
          <option>1m</option>
          <option>5m</option>
          <option>15m</option>
          <option>1h</option>
          <option>4h</option>
          <option>1d</option>
        </select>
      </label>
    </div>
    <div id="performanceBox" class="empty">هنوز گزارشی گرفته نشده است.</div>
  `;
  reportPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadPerformanceBtn").addEventListener("click", loadPerformance);
  applyPerformanceLanguage();
}

function applyPerformanceLanguage() {
  const panel = document.getElementById("performancePanel");
  if (!panel) return;
  panel.querySelector(".panelHeader h2").textContent = pt("title");
  panel.querySelector(".panelHeader .hint").textContent = pt("hint");
  document.getElementById("loadPerformanceBtn").textContent = pt("load");
  const daysLabel = panel.querySelector('label:has(#performanceDays)');
  if (daysLabel?.firstChild) daysLabel.firstChild.textContent = `${pt("days")}\n`;
  const timeframeLabel = panel.querySelector('label:has(#performanceTimeframe)');
  if (timeframeLabel?.firstChild) timeframeLabel.firstChild.textContent = `${pt("timeframe")}\n`;
  const firstOption = document.querySelector("#performanceTimeframe option[value='']");
  if (firstOption) firstOption.textContent = pt("all");
  const box = document.getElementById("performanceBox");
  if (box && box.className === "empty" && !lastPerformanceData) box.textContent = pt("empty");
  if (lastPerformanceData) renderPerformance(lastPerformanceData);
}

function renderPerformance(data) {
  lastPerformanceData = data;
  const timeframeRows = Object.entries(data.by_timeframe || {}).map(([timeframe, item]) => `
    <tr>
      <td>${timeframe}</td>
      <td>${item.total}</td>
      <td>${item.correct}</td>
      <td>${item.wrong}</td>
      <td>${item.neutral}</td>
      <td>${item.accuracy}%</td>
    </tr>
  `).join("");
  const recentRows = (data.recent || []).slice(0, 20).map((item) => `
    <tr>
      <td>${item.symbol}</td>
      <td>${item.timeframe}</td>
      <td><span class="badge ${String(item.signal).toLowerCase()}">${item.signal}</span></td>
      <td><span class="badge ${String(item.status).toLowerCase()}">${item.status}</span></td>
      <td>${item.outcome_percent ?? "-"}</td>
      <td>${(typeof currentLanguage === "function" && currentLanguage() === "en" ? item.advice_en : item.advice_fa) || "-"}</td>
    </tr>
  `).join("");
  document.getElementById("performanceBox").className = "reportBox";
  document.getElementById("performanceBox").innerHTML = `
    <div class="summaryGrid">
      <div><span>${pt("total")}</span><b>${data.total}</b></div>
      <div><span>${pt("reviewed")}</span><b>${data.reviewed}</b></div>
      <div><span>${pt("correct")}</span><b>${data.correct}</b></div>
      <div><span>${pt("wrong")}</span><b>${data.wrong}</b></div>
      <div><span>${pt("neutral")}</span><b>${data.neutral}</b></div>
      <div><span>${pt("pending")}</span><b>${data.pending}</b></div>
      <div><span>${pt("accuracy")}</span><b>${data.accuracy}%</b></div>
      <div><span>${pt("range")}</span><b>${data.days}d</b></div>
    </div>
    <div class="tableWrap">
      <table>
        <thead><tr><th>${pt("timeframe")}</th><th>${pt("total")}</th><th>${pt("correct")}</th><th>${pt("wrong")}</th><th>${pt("neutral")}</th><th>${pt("accuracy")}</th></tr></thead>
        <tbody>${timeframeRows || `<tr><td colspan='6'>${pt("noData")}</td></tr>`}</tbody>
      </table>
    </div>
    <div class="tableWrap performanceRecent">
      <table>
        <thead><tr><th>${pt("symbol")}</th><th>TF</th><th>${pt("signal")}</th><th>${pt("result")}</th><th>${pt("percent")}</th><th>${pt("drawdown")}</th></tr></thead>
        <tbody>${recentRows || `<tr><td colspan='6'>${pt("noData")}</td></tr>`}</tbody>
      </table>
    </div>
  `;
}

async function loadPerformance() {
  try {
    const days = document.getElementById("performanceDays").value || 7;
    const timeframe = document.getElementById("performanceTimeframe").value;
    const query = new URLSearchParams({ days });
    if (timeframe) query.set("timeframe", timeframe);
    document.getElementById("performanceBox").className = "empty";
    document.getElementById("performanceBox").textContent = pt("loading");
    const data = await api(`/performance/signals?${query.toString()}`);
    renderPerformance(data);
  } catch (error) {
    document.getElementById("performanceBox").className = "empty";
    document.getElementById("performanceBox").textContent = error.message;
  }
}

ensurePerformancePanel();
window.addEventListener("market-ai-language-change", applyPerformanceLanguage);
