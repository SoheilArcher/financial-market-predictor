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
}

function renderPerformance(data) {
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
      <td>${item.advice_fa || "-"}</td>
    </tr>
  `).join("");
  document.getElementById("performanceBox").className = "reportBox";
  document.getElementById("performanceBox").innerHTML = `
    <div class="summaryGrid">
      <div><span>کل سیگنال‌ها</span><b>${data.total}</b></div>
      <div><span>بررسی‌شده</span><b>${data.reviewed}</b></div>
      <div><span>درست</span><b>${data.correct}</b></div>
      <div><span>غلط</span><b>${data.wrong}</b></div>
      <div><span>خنثی</span><b>${data.neutral}</b></div>
      <div><span>در انتظار</span><b>${data.pending}</b></div>
      <div><span>دقت</span><b>${data.accuracy}%</b></div>
      <div><span>بازه</span><b>${data.days}d</b></div>
    </div>
    <div class="tableWrap">
      <table>
        <thead><tr><th>تایم‌فریم</th><th>کل</th><th>درست</th><th>غلط</th><th>خنثی</th><th>دقت</th></tr></thead>
        <tbody>${timeframeRows || "<tr><td colspan='6'>داده‌ای نیست</td></tr>"}</tbody>
      </table>
    </div>
    <div class="tableWrap performanceRecent">
      <table>
        <thead><tr><th>نماد</th><th>TF</th><th>سیگنال</th><th>نتیجه</th><th>درصد</th><th>اگر رفت تو ضرر</th></tr></thead>
        <tbody>${recentRows || "<tr><td colspan='6'>داده‌ای نیست</td></tr>"}</tbody>
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
    document.getElementById("performanceBox").textContent = "در حال ارزیابی سیگنال‌ها...";
    const data = await api(`/performance/signals?${query.toString()}`);
    renderPerformance(data);
  } catch (error) {
    document.getElementById("performanceBox").className = "empty";
    document.getElementById("performanceBox").textContent = error.message;
  }
}

ensurePerformancePanel();
