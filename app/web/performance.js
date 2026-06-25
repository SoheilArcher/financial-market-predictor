let lastModelPerformance = null;

const modelPerformanceText = {
  fa: {
    title: "Model Performance",
    hint: "ارزیابی واقعی سیگنال‌های غیر WAIT بر اساس کندل‌های بعد از صدور تحلیل.",
    evaluate: "Evaluate Pending",
    refresh: "بروزرسانی",
    symbol: "نماد",
    timeframe: "تایم‌فریم",
    all: "همه",
    total: "کل سیگنال‌ها",
    winRate: "Win Rate",
    averagePnl: "میانگین PnL",
    wins: "برد",
    losses: "باخت",
    expired: "منقضی",
    noData: "بدون داده",
    lastSignals: "آخرین سیگنال‌ها",
    direction: "جهت",
    confidence: "اعتماد",
    entry: "ورود",
    sl: "SL",
    tp: "TP",
    result: "نتیجه",
    pnl: "PnL",
    reason: "دلیل",
    empty: "هنوز سیگنال قابل ارزیابی ثبت نشده است.",
    loading: "در حال دریافت عملکرد مدل...",
    evaluating: "در حال ارزیابی سیگنال‌های معلق...",
  },
  en: {
    title: "Model Performance",
    hint: "Real evaluation of non-WAIT signals using candles after each prediction.",
    evaluate: "Evaluate Pending",
    refresh: "Refresh",
    symbol: "Symbol",
    timeframe: "Timeframe",
    all: "All",
    total: "Total signals",
    winRate: "Win rate",
    averagePnl: "Average PnL",
    wins: "Wins",
    losses: "Losses",
    expired: "Expired",
    noData: "No data",
    lastSignals: "Last signals",
    direction: "Direction",
    confidence: "Confidence",
    entry: "Entry",
    sl: "SL",
    tp: "TP",
    result: "Result",
    pnl: "PnL",
    reason: "Reason",
    empty: "No evaluable signals have been recorded yet.",
    loading: "Loading model performance...",
    evaluating: "Evaluating pending signals...",
  },
};

function mp(key) {
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  return modelPerformanceText[lang]?.[key] || modelPerformanceText.fa[key] || key;
}

function ensureModelPerformancePanel() {
  if (document.getElementById("performancePanel")) return;
  const reportPanel = document.getElementById("reportForm")?.closest(".panel");
  if (!reportPanel) return;
  const panel = document.createElement("section");
  panel.id = "performancePanel";
  panel.className = "panel dashboardBlock";
  panel.dataset.blockId = "performance";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>${mp("title")}</h2>
        <p class="hint">${mp("hint")}</p>
      </div>
      <div class="performanceActions">
        <button id="evaluatePendingBtn" class="ghost" type="button">${mp("evaluate")}</button>
        <button id="loadPerformanceBtn" class="primary" type="button">${mp("refresh")}</button>
      </div>
    </div>
    <div class="performanceTools">
      <label>
        <span>${mp("symbol")}</span>
        <input id="performanceSymbol" placeholder="BTCUSDT" />
      </label>
      <label>
        <span>${mp("timeframe")}</span>
        <select id="performanceTimeframe">
          <option value="">${mp("all")}</option>
          <option>1m</option>
          <option>5m</option>
          <option>15m</option>
          <option>1h</option>
          <option>4h</option>
          <option>1d</option>
        </select>
      </label>
    </div>
    <div id="performanceBox" class="empty">${mp("empty")}</div>
  `;
  reportPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadPerformanceBtn").addEventListener("click", loadModelPerformance);
  document.getElementById("evaluatePendingBtn").addEventListener("click", evaluatePendingPerformance);
}

function applyModelPerformanceLanguage() {
  const panel = document.getElementById("performancePanel");
  if (!panel) return;
  panel.querySelector(".panelHeader h2").textContent = mp("title");
  panel.querySelector(".panelHeader .hint").textContent = mp("hint");
  document.getElementById("evaluatePendingBtn").textContent = mp("evaluate");
  document.getElementById("loadPerformanceBtn").textContent = mp("refresh");
  panel.querySelector("label:nth-child(1) span").textContent = mp("symbol");
  panel.querySelector("label:nth-child(2) span").textContent = mp("timeframe");
  panel.querySelector("#performanceTimeframe option[value='']").textContent = mp("all");
  if (lastModelPerformance) renderModelPerformance(lastModelPerformance);
}

function formatPercent(value) {
  const number = Number(value || 0);
  return `${number.toFixed(2)}%`;
}

function statCard(label, value, extraClass = "") {
  return `<div class="performanceStat ${extraClass}"><span>${label}</span><b>${value}</b></div>`;
}

function renderModelPerformance(data) {
  lastModelPerformance = data;
  const rows = (data.last_90_signals || []).map((item) => `
    <tr>
      <td>${item.symbol}</td>
      <td>${item.timeframe}</td>
      <td><span class="badge ${String(item.direction).toLowerCase()}">${item.direction}</span></td>
      <td>${item.confidence ?? 0}</td>
      <td>${item.entry_price ?? "-"}</td>
      <td>${item.stop_loss ?? "-"}</td>
      <td>${item.take_profit ?? "-"}</td>
      <td><span class="badge ${String(item.result).toLowerCase()}">${item.result}</span></td>
      <td>${item.pnl_percent ?? "-"}</td>
      <td>${item.reason_fa || "-"}</td>
    </tr>
  `).join("");

  const box = document.getElementById("performanceBox");
  box.className = "reportBox";
  box.innerHTML = `
    <div class="performanceStats">
      ${statCard(mp("total"), data.total_signals)}
      ${statCard(mp("winRate"), formatPercent(data.win_rate), "win")}
      ${statCard(mp("averagePnl"), formatPercent(data.average_pnl_percent))}
      ${statCard(mp("wins"), data.win_count, "win")}
      ${statCard(mp("losses"), data.loss_count, "loss")}
      ${statCard(mp("expired"), data.expired_count, "expired")}
      ${statCard(mp("noData"), data.no_data_count ?? 0, "nodata")}
    </div>
    <div class="performanceBreakdowns">
      <div><b>Best</b><span>${data.best_symbol || "-"}</span></div>
      <div><b>Worst</b><span>${data.worst_symbol || "-"}</span></div>
      <div><b>FA</b><span>${data.summary_fa || ""}</span></div>
    </div>
    <div class="tableWrap performanceRecent">
      <h3>${mp("lastSignals")}</h3>
      <table>
        <thead>
          <tr>
            <th>${mp("symbol")}</th><th>TF</th><th>${mp("direction")}</th><th>${mp("confidence")}</th>
            <th>${mp("entry")}</th><th>${mp("sl")}</th><th>${mp("tp")}</th><th>${mp("result")}</th><th>${mp("pnl")}</th><th>${mp("reason")}</th>
          </tr>
        </thead>
        <tbody>${rows || `<tr><td colspan="10">${mp("empty")}</td></tr>`}</tbody>
      </table>
    </div>
  `;
}

function performanceQuery() {
  const query = new URLSearchParams();
  const symbol = document.getElementById("performanceSymbol")?.value.trim();
  const timeframe = document.getElementById("performanceTimeframe")?.value;
  if (symbol) query.set("symbol", symbol.toUpperCase());
  if (timeframe) query.set("timeframe", timeframe);
  return query.toString();
}

async function loadModelPerformance() {
  const box = document.getElementById("performanceBox");
  try {
    box.className = "empty";
    box.textContent = mp("loading");
    const query = performanceQuery();
    const data = await api(`/performance/summary${query ? `?${query}` : ""}`);
    renderModelPerformance(data);
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

async function evaluatePendingPerformance() {
  const box = document.getElementById("performanceBox");
  try {
    box.className = "empty";
    box.textContent = mp("evaluating");
    await api("/performance/evaluate-pending", { method: "POST" });
    await loadModelPerformance();
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

ensureModelPerformancePanel();
window.addEventListener("market-ai-language-change", applyModelPerformanceLanguage);
