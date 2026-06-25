function renderChartAnalysis(analysis) {
  const box = document.getElementById("chartAnalysisBox");
  if (!box) return;
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  const label = (fa, en) => (lang === "en" ? en : fa);
  const levels = analysis.levels || {};
  const indicators = analysis.indicators || {};
  const reasons = analysis.reasons || [];
  const live = analysis.live_price || {};
  box.innerHTML = `
    <div class="chartAnalysisHeader">
      <span class="badge ${String(analysis.signal || "wait").toLowerCase()}">${analysis.signal || "-"}</span>
      <div>
        <b>${analysis.summary_fa || analysis.message || ""}</b>
        <p>${analysis.pair_explanation_fa || ""}</p>
      </div>
    </div>
    <div class="chartAnalysisMetrics">
      <span>${label("قیمت", "Price")}: <b>${analysis.price ?? live.price ?? "-"}</b> ${live.quote_asset || ""}</span>
      <span>${label("اعتماد", "Confidence")}: <b>${analysis.confidence ?? 0}%</b></span>
      <span>RSI: <b>${indicators.rsi ?? "-"}</b></span>
      <span>${label("روند", "Trend")}: <b>${indicators.trend ?? "-"}</b></span>
      <span>${label("حمایت", "Support")}: <b>${levels.support ?? "-"}</b></span>
      <span>${label("مقاومت", "Resistance")}: <b>${levels.resistance ?? "-"}</b></span>
      <span>SL: <b>${levels.stop_loss ?? "-"}</b></span>
      <span>TP: <b>${levels.take_profit ?? "-"}</b></span>
    </div>
    <ul>${reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>
  `;
}

async function loadChart() {
  const symbol = document.getElementById("chartSymbol").value.trim().toUpperCase();
  const timeframe = document.getElementById("chartTimeframe").value;
  const chartMeta = document.getElementById("chartMeta");
  chartMeta.textContent = "در حال دریافت داده و رسم چارت...";

  const data = await api(`/chart/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(timeframe)}&limit=150`);
  chartMeta.dataset.lastChart = JSON.stringify(data);
  renderPriceChart(data);
  renderRsiChart(data);

  const last = data.last;
  const live = data.live_price || {};
  const liveLocale = typeof currentLanguage === "function" && currentLanguage() === "en" ? "en-US" : "fa-IR";
  const label = (fa, en) => (typeof currentLanguage === "function" && currentLanguage() === "en" ? en : fa);
  const liveTime = live.fetched_at
    ? new Date(live.fetched_at).toLocaleTimeString(liveLocale)
    : "-";
  chartMeta.innerHTML = `
    <b>${data.symbol}</b>
    <span>${data.timeframe}</span>
    <span>${label("قیمت زنده", "Live")}: ${live.price ?? "-"} ${live.quote_asset || ""}</span>
    <span>${label("کلوز", "Close")}: ${last ? last.close : "-"}</span>
    <span>${label("بروزرسانی", "Updated")}: ${liveTime}</span>
    <span>EMA20 / EMA50 / RSI آنلاین</span>
  `;
  const analysis = await api(`/market/analyze/Binance/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(timeframe)}&limit=150`);
  renderChartAnalysis(analysis);
  if (typeof renderReasonsFromAnalysis === "function") {
    renderReasonsFromAnalysis(analysis);
  }
  await refreshMe();
}

document.getElementById("chartForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await loadChart();
  } catch (error) {
    document.getElementById("chartMeta").textContent = error.message;
  }
});

window.addEventListener("resize", () => {
  const meta = document.getElementById("chartMeta");
  if (!meta.dataset.lastChart) return;
  try {
    const data = JSON.parse(meta.dataset.lastChart);
    renderPriceChart(data);
    renderRsiChart(data);
  } catch {
    // Ignore stale chart cache.
  }
});
