(function () {
  let monitorTimer = null;
  let lastMonitorAction = "";

  function label(fa, en) {
    return typeof currentLanguage === "function" && currentLanguage() === "en" ? en : fa;
  }

  function ensureTradePanel() {
    if (document.getElementById("tradePlanPanel")) return;
    const analysisPanel = document.querySelector('[data-block-id="analysis"]');
    if (!analysisPanel) return;
    const panel = document.createElement("section");
    panel.id = "tradePlanPanel";
    panel.className = "panel dashboardBlock";
    panel.dataset.blockId = "trade-plan";
    panel.innerHTML = `
      <div class="panelHeader">
        <div>
          <h2>${label("پلن معامله و مدیریت ریسک", "Trade Plan and Risk")}</h2>
          <p class="hint">${label("نقطه ورود، خروج، حد ضرر، تارگت‌ها و پایش وضعیت معامله", "Entry, exit, stop loss, targets and live monitoring")}</p>
        </div>
        <button id="toggleMonitorBtn" class="ghost" type="button">${label("فعال کردن پایش", "Start Monitor")}</button>
      </div>
      <form id="tradePlanForm" class="tradeTools">
        <label>${label("صرافی", "Exchange")}<input id="tradeExchange" value="Binance" /></label>
        <label>${label("نماد", "Symbol")}<input id="tradeSymbol" value="BTCUSDT" /></label>
        <label>${label("تایم‌فریم", "Timeframe")}
          <select id="tradeTimeframe">
            <option>1m</option><option selected>5m</option><option>15m</option><option>1h</option><option>4h</option><option>1d</option>
          </select>
        </label>
        <label>${label("سرمایه", "Account")}<input id="tradeAccountSize" type="number" min="1" value="1000" /></label>
        <label>${label("ریسک ٪", "Risk %")}<input id="tradeRiskPercent" type="number" min="0.1" max="5" step="0.1" value="1" /></label>
        <label>${label("قیمت ورود باز", "Open Entry")}<input id="tradeEntryPrice" type="number" min="0" step="0.0001" placeholder="اختیاری" /></label>
        <label>${label("جهت باز", "Open Side")}
          <select id="tradeSide">
            <option value="">Auto</option><option value="LONG">LONG</option><option value="SHORT">SHORT</option>
          </select>
        </label>
        <button class="primary" type="submit">${label("ساخت پلن", "Build Plan")}</button>
      </form>
      <div id="tradePlanBox" class="empty">${label("پلن معامله اینجا نمایش داده می‌شود.", "Trade plan appears here.")}</div>
    `;
    analysisPanel.insertAdjacentElement("afterend", panel);
    document.getElementById("tradePlanForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await loadTradePlan();
    });
    document.getElementById("toggleMonitorBtn").addEventListener("click", toggleMonitor);
  }

  function tradeQuery() {
    const symbol = document.getElementById("tradeSymbol").value.trim().toUpperCase();
    const params = new URLSearchParams({
      exchange: document.getElementById("tradeExchange").value.trim() || "Binance",
      timeframe: document.getElementById("tradeTimeframe").value,
      account_size: document.getElementById("tradeAccountSize").value || "1000",
      risk_percent: document.getElementById("tradeRiskPercent").value || "1",
      limit: "150",
    });
    const entry = document.getElementById("tradeEntryPrice").value;
    const side = document.getElementById("tradeSide").value;
    if (entry) params.set("entry_price", entry);
    if (side) params.set("side", side);
    return { symbol, params };
  }

  async function loadTradePlan(silent = false) {
    const box = document.getElementById("tradePlanBox");
    const { symbol, params } = tradeQuery();
    if (!symbol) return null;
    if (!silent) {
      box.className = "empty";
      box.textContent = label("در حال ساخت پلن معامله...", "Building trade plan...");
    }
    const data = await api(`/trade/plan/${encodeURIComponent(symbol)}?${params.toString()}`);
    renderTradePlan(data);
    if (data.monitor && data.monitor.action !== "HOLD") notifyTrade(data.monitor);
    return data;
  }

  function renderTradePlan(data) {
    const box = document.getElementById("tradePlanBox");
    const plan = data.plan || {};
    const sizing = data.position_sizing || {};
    const monitor = data.monitor;
    const standard = data.exchange_standard || {};
    if (data.trade_status === "NO_TRADE") {
      box.className = "tradePlanBox";
      box.innerHTML = `
        <div class="tradeStatus wait"><b>${label("فعلاً ورود نکن", "No Trade")}</b><span>${data.summary_fa}</span></div>
        <ul>${(data.alerts || []).map((item) => `<li>${item}</li>`).join("")}</ul>
        <div class="exchangeStandard"><b>${standard.name || "-"}</b><span>${standard.message_fa || standard.notes_fa?.[0] || ""}</span></div>
      `;
      return;
    }
    box.className = "tradePlanBox";
    box.innerHTML = `
      <div class="tradeStatus ${String(data.side || "").toLowerCase()}">
        <b>${data.side} ${data.symbol}</b>
        <span>${label("اعتماد", "Confidence")}: ${data.confidence}% | ${label("ریسک", "Risk")}: ${data.risk}</span>
      </div>
      <div class="tradeGrid">
        <div><span>${label("ورود از", "Entry From")}</span><b>${plan.entry_zone?.from ?? "-"}</b></div>
        <div><span>${label("ورود تا", "Entry To")}</span><b>${plan.entry_zone?.to ?? "-"}</b></div>
        <div><span>SL</span><b>${plan.stop_loss ?? "-"}</b></div>
        ${(plan.take_profits || []).map((tp) => `<div><span>${tp.name}</span><b>${tp.price}</b></div>`).join("")}
      </div>
      <div class="tradeGrid">
        <div><span>${label("ریسک دلاری", "Risk Amount")}</span><b>${sizing.risk_amount ?? "-"}</b></div>
        <div><span>${label("حجم پیشنهادی", "Suggested Qty")}</span><b>${sizing.suggested_quantity ?? "-"}</b></div>
        <div><span>${label("ارزش معامله", "Notional")}</span><b>${sizing.notional_value ?? "-"}</b></div>
      </div>
      ${monitor ? `<div class="monitorBox ${monitor.severity}"><b>${monitor.action}</b><span>${monitor.message_fa}</span><small>PNL: ${monitor.pnl_percent}%</small></div>` : ""}
      <div class="tradeRules">
        <b>${label("اگر خلاف جهت رفت", "If It Goes Against You")}</b>
        <p>${plan.if_price_goes_against?.close_rule || ""}</p>
        <p>${plan.if_price_goes_against?.default_action || ""}</p>
        <p>${plan.if_price_goes_against?.dca_rule || ""}</p>
      </div>
      <div class="exchangeStandard">
        <b>${standard.name || "-"}</b>
        <span>${label("حداکثر ریسک", "Max Risk")}: ${standard.max_risk_per_trade_percent}% | ${label("لوریج پیشنهادی", "Suggested Leverage")}: ${standard.max_leverage}x | ${standard.known ? label("استاندارد ثبت شده", "Known standard") : label("نیازمند ثبت استاندارد", "Needs review")}</span>
      </div>
      <ul>${(data.alerts || []).map((item) => `<li>${item}</li>`).join("")}</ul>
    `;
  }

  async function toggleMonitor() {
    const button = document.getElementById("toggleMonitorBtn");
    if (monitorTimer) {
      clearInterval(monitorTimer);
      monitorTimer = null;
      button.textContent = label("فعال کردن پایش", "Start Monitor");
      return;
    }
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
    await loadTradePlan();
    monitorTimer = window.setInterval(async () => {
      try {
        await loadTradePlan(true);
      } catch (error) {
        console.warn(error);
      }
    }, 60000);
    button.textContent = label("توقف پایش", "Stop Monitor");
  }

  function notifyTrade(monitor) {
    const key = `${monitor.action}:${monitor.current_price}`;
    if (key === lastMonitorAction) return;
    lastMonitorAction = key;
    const message = monitor.message_fa;
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("Market AI", { body: message });
    } else if (typeof toast === "function") {
      toast(message);
    }
  }

  window.addEventListener("DOMContentLoaded", ensureTradePanel);
})();
