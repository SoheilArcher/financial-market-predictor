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
  const liveTime = live.fetched_at
    ? new Date(live.fetched_at).toLocaleTimeString(liveLocale)
    : "-";
  chartMeta.innerHTML = `
    <b>${data.symbol}</b>
    <span>${data.timeframe}</span>
    <span>Live: ${live.price ?? "-"} ${live.quote_asset || ""}</span>
    <span>Close: ${last ? last.close : "-"}</span>
    <span>Updated: ${liveTime}</span>
    <span>EMA20 / EMA50 / RSI آنلاین</span>
  `;
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
