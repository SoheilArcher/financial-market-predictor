const uiText = {
  fa: {
    language: "زبان",
    feedbackTitle: "نظر مشتری",
    feedbackHint: "نظر یا برداشت خودت را درباره این تحلیل ثبت کن.",
    feedbackPlaceholder: "مثلاً: به نظرم این فروش هنوز تایید کافی ندارد...",
    send: "ثبت نظر",
    load: "نمایش نظرها",
    reasonsTitle: "چرا این تحلیل؟",
    reasonsEmpty: "بعد از اجرای چارت یا تحلیل، دلیل‌ها اینجا نمایش داده می‌شود.",
    commentsEmpty: "هنوز نظری ثبت نشده است.",
    saved: "نظر ثبت شد.",
    marketView: "نمای زنده بازار، سیگنال‌ها و مدیریت اشتراک",
    chartTitle: "چارت زنده",
    reportTitle: "گزارش کلی بازار",
    singleTitle: "تحلیل تک‌نماد",
    loginRegister: "ورود / ثبت‌نام",
    authHint: "برای دیدن چارت، گزارش‌ها و ابزارهای مدیریت سرمایه وارد حساب خود شوید.",
    authIntro: "تحلیل بازار، گزارش عملکرد مدل و برنامه معامله در یک محیط یکپارچه.",
    login: "ورود",
    register: "ثبت‌نام",
    email: "ایمیل",
    password: "رمز عبور",
    showPassword: "نمایش رمز عبور",
    hidePassword: "مخفی کردن رمز عبور",
    name: "نام",
    country: "اهل کجایی؟",
    continue: "ادامه",
    logout: "خروج",
    account: "حساب کاربری",
    subscription: "اشتراک من",
    refresh: "بروزرسانی",
    chartHint: "کندل‌ها همراه با EMA20، EMA50 و RSI",
    symbol: "نماد",
    timeframe: "تایم‌فریم",
    showChart: "نمایش چارت",
    reportHint: "اسکن چند نماد اصلی، خلاصه جهت بازار و رتبه‌بندی سیگنال‌ها",
    symbols: "نمادها",
    buildReport: "ساخت گزارش",
    exchange: "صرافی",
    analyze: "تحلیل",
    adminUsers: "مدیریت کاربران",
    loadInfo: "دریافت اطلاعات",
    userId: "شناسه کاربر",
    plan: "پلن",
    days: "روز",
    assignPlan: "اختصاص اشتراک",
    analysisPlaceholder: "خروجی تحلیل اینجا نمایش داده می‌شود.",
    reportPlaceholder: "گزارش کلی بازار اینجا نمایش داده می‌شود.",
    chartLoginHint: "برای دریافت چارت وارد حساب شوید و اشتراک فعال داشته باشید.",
  },
  en: {
    language: "Language",
    feedbackTitle: "Customer Feedback",
    feedbackHint: "Add your opinion or objection about this analysis.",
    feedbackPlaceholder: "Example: I think this short signal still needs confirmation...",
    send: "Post Comment",
    load: "Load Comments",
    reasonsTitle: "Why this analysis?",
    reasonsEmpty: "Run a chart or analysis to see the reasoning here.",
    commentsEmpty: "No comments yet.",
    saved: "Comment saved.",
    marketView: "Live market view, signals, and subscription management",
    chartTitle: "Live Chart",
    reportTitle: "Market-Wide Report",
    singleTitle: "Single Symbol Analysis",
    loginRegister: "Login / Register",
    authHint: "Log in to access charts, reports, and capital management tools.",
    authIntro: "Market analysis, model performance, and trade planning in one workspace.",
    login: "Login",
    register: "Register",
    email: "Email",
    password: "Password",
    showPassword: "Show password",
    hidePassword: "Hide password",
    name: "Name",
    country: "Where are you from?",
    continue: "Continue",
    logout: "Logout",
    account: "Account",
    subscription: "My Subscription",
    refresh: "Refresh",
    chartHint: "Candles with EMA20, EMA50, and RSI",
    symbol: "Symbol",
    timeframe: "Timeframe",
    showChart: "Show Chart",
    reportHint: "Scan major symbols, market direction, and signal ranking",
    symbols: "Symbols",
    buildReport: "Build Report",
    exchange: "Exchange",
    analyze: "Analyze",
    adminUsers: "User Management",
    loadInfo: "Load Data",
    userId: "User ID",
    plan: "Plan",
    days: "Days",
    assignPlan: "Assign Plan",
    analysisPlaceholder: "Analysis output will appear here.",
    reportPlaceholder: "Market-wide report will appear here.",
    chartLoginHint: "Log in and activate a subscription to load the chart.",
  },
};

function currentLanguage() {
  return localStorage.getItem("market_ai_lang") || "fa";
}

function t(key) {
  return uiText[currentLanguage()][key] || uiText.fa[key] || key;
}

function addLanguageSelector() {
  const topbar = document.querySelector(".topbar");
  if (!topbar || document.getElementById("languageSelect")) return;
  const wrapper = document.createElement("div");
  wrapper.className = "languageBox";
  wrapper.innerHTML = `
    <label>
      <span id="languageLabel">${t("language")}</span>
      <select id="languageSelect">
        <option value="fa">فارسی</option>
        <option value="en">English</option>
      </select>
    </label>
  `;
  topbar.appendChild(wrapper);
  document.getElementById("languageSelect").value = currentLanguage();
  document.getElementById("languageSelect").addEventListener("change", (event) => {
    localStorage.setItem("market_ai_lang", event.target.value);
    applyLanguage();
  });
}

function applyLanguage() {
  const lang = currentLanguage();
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
  document.title = lang === "fa" ? "پلتفرم هوش بازار" : "Market AI Platform";
  const setText = (selector, value) => {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  };
  const setLabel = (selector, value) => {
    const element = document.querySelector(selector);
    if (element && element.firstChild) element.firstChild.textContent = `${value}\n`;
  };
  const sessionText = document.getElementById("sessionText");
  if (sessionText && !(window.state && state.token)) sessionText.textContent = t("marketView");
  setText("#authForm .panelHeader h2", t("loginRegister"));
  setText("#authForm .panelHeader .hint", t("authHint"));
  setText(".authIntro span", t("authIntro"));
  setText('[data-auth-mode="login"]', t("login"));
  setText('[data-auth-mode="register"]', t("register"));
  setLabel('label:has(#email)', t("email"));
  setLabel('label:has(#password)', t("password"));
  const togglePasswordBtn = document.getElementById("togglePasswordBtn");
  if (togglePasswordBtn) {
    togglePasswordBtn.setAttribute("aria-label", document.getElementById("password")?.type === "text" ? t("hidePassword") : t("showPassword"));
  }
  setLabel("#nameField", t("name"));
  setLabel("#countryField", t("country"));
  setText("#authForm button.primary", t("continue"));
  setText("#logoutBtn", t("logout"));
  setText("#accountPanel h2", t("account"));
  setText("#refreshMeBtn", t("refresh"));
  const subscriptionTitle = Array.from(document.querySelectorAll(".panelHeader h2")).find((item) => item.textContent.includes("اشتراک") || item.textContent.includes("Subscription"));
  if (subscriptionTitle) subscriptionTitle.textContent = t("subscription");
  const chartHeader = document.getElementById("chartForm")?.closest(".panel")?.querySelector(".panelHeader");
  if (chartHeader) {
    chartHeader.querySelector("h2").textContent = t("chartTitle");
    chartHeader.querySelector(".hint").textContent = t("chartHint");
  }
  setLabel('label:has(#chartSymbol)', t("symbol"));
  setLabel('label:has(#chartTimeframe)', t("timeframe"));
  setText("#chartForm button.primary", t("showChart"));
  const chartMeta = document.getElementById("chartMeta");
  if (chartMeta && !chartMeta.dataset.lastChart) chartMeta.textContent = t("chartLoginHint");
  const reportHeader = document.getElementById("reportForm")?.closest(".panel")?.querySelector(".panelHeader");
  if (reportHeader) {
    reportHeader.querySelector("h2").textContent = t("reportTitle");
    reportHeader.querySelector(".hint").textContent = t("reportHint");
  }
  setLabel('label:has(#reportSymbols)', t("symbols"));
  setLabel('label:has(#reportTimeframe)', t("timeframe"));
  setText("#reportForm button.primary", t("buildReport"));
  const marketReportBox = document.getElementById("marketReportBox");
  if (marketReportBox && marketReportBox.className === "empty") marketReportBox.textContent = t("reportPlaceholder");
  const analysisHeader = document.getElementById("analysisForm")?.closest(".panel")?.querySelector(".panelHeader");
  if (analysisHeader) analysisHeader.querySelector("h2").textContent = t("singleTitle");
  setLabel('label:has(#exchange)', t("exchange"));
  setLabel('label:has(#symbol)', t("symbol"));
  setLabel('label:has(#timeframe)', t("timeframe"));
  setText("#analysisForm button.primary", t("analyze"));
  const analysisResult = document.getElementById("analysisResult");
  if (analysisResult && analysisResult.textContent.includes("خروجی تحلیل")) analysisResult.textContent = t("analysisPlaceholder");
  setText("#adminPanel .panelHeader h2", t("adminUsers"));
  setText("#loadAdminBtn", t("loadInfo"));
  setLabel('label:has(#targetUserId)', t("userId"));
  setLabel('label:has(#targetPlan)', t("plan"));
  setLabel('label:has(#targetDays)', t("days"));
  setText("#assignPlanBtn", t("assignPlan"));
  const languageLabel = document.getElementById("languageLabel");
  if (languageLabel) languageLabel.textContent = t("language");
  const feedbackTitle = document.getElementById("feedbackTitle");
  if (feedbackTitle) feedbackTitle.textContent = t("feedbackTitle");
  const feedbackHint = document.getElementById("feedbackHint");
  if (feedbackHint) feedbackHint.textContent = t("feedbackHint");
  const commentInput = document.getElementById("commentInput");
  if (commentInput) commentInput.placeholder = t("feedbackPlaceholder");
  const sendCommentBtn = document.getElementById("sendCommentBtn");
  if (sendCommentBtn) sendCommentBtn.textContent = t("send");
  const loadCommentsBtn = document.getElementById("loadCommentsBtn");
  if (loadCommentsBtn) loadCommentsBtn.textContent = t("load");
  const reasonsTitle = document.getElementById("reasonsTitle");
  if (reasonsTitle) reasonsTitle.textContent = t("reasonsTitle");
  const reasonsBox = document.getElementById("reasonsBox");
  if (reasonsBox && reasonsBox.dataset.empty === "1") reasonsBox.textContent = t("reasonsEmpty");
  window.dispatchEvent(new CustomEvent("market-ai-language-change", { detail: { lang } }));
}

function addReasonAndFeedbackPanel() {
  if (document.getElementById("feedbackPanel")) return;
  const chartPanel = document.getElementById("chartForm")?.closest(".panel");
  if (!chartPanel) return;

  const panel = document.createElement("section");
  panel.id = "feedbackPanel";
  panel.className = "panel dashboardBlock";
  panel.dataset.blockId = "feedback";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2 id="reasonsTitle">${t("reasonsTitle")}</h2>
        <p id="feedbackHint">${t("feedbackHint")}</p>
      </div>
      <span id="feedbackTarget" class="badge">BTCUSDT</span>
    </div>
    <div id="reasonsBox" class="reasonBox" data-empty="1">${t("reasonsEmpty")}</div>
    <div class="feedbackComposer">
      <h2 id="feedbackTitle">${t("feedbackTitle")}</h2>
      <textarea id="commentInput" rows="4" placeholder="${t("feedbackPlaceholder")}"></textarea>
      <div class="feedbackActions">
        <button id="sendCommentBtn" class="primary" type="button">${t("send")}</button>
        <button id="loadCommentsBtn" class="ghost" type="button">${t("load")}</button>
      </div>
    </div>
    <div id="commentsBox" class="commentsBox">${t("commentsEmpty")}</div>
  `;
  chartPanel.insertAdjacentElement("afterend", panel);

  document.getElementById("sendCommentBtn").addEventListener("click", saveComment);
  document.getElementById("loadCommentsBtn").addEventListener("click", loadComments);
}

function activeFeedbackTarget() {
  const symbol = (document.getElementById("chartSymbol")?.value || document.getElementById("symbol")?.value || "BTCUSDT")
    .trim()
    .toUpperCase();
  return {
    target_type: "symbol_analysis",
    target_id: symbol,
  };
}

function renderReasonsFromAnalysis(analysis) {
  const reasonsBox = document.getElementById("reasonsBox");
  if (!reasonsBox) return;
  const reasons = analysis?.reasons || [];
  const levels = analysis?.levels || {};
  const indicators = analysis?.indicators || {};
  const live = analysis?.live_price || {};
  const label = (fa, en) => (currentLanguage() === "fa" ? fa : en);
  const liveTime = live.fetched_at
    ? new Date(live.fetched_at).toLocaleTimeString(currentLanguage() === "fa" ? "fa-IR" : "en-US")
    : "-";
  reasonsBox.dataset.empty = "0";
  reasonsBox.innerHTML = `
    <div class="reasonHeadline">
      <span class="badge ${(analysis.signal || "wait").toLowerCase()}">${analysis.signal || "-"}</span>
      <b>${analysis.summary_fa || analysis.message || ""}</b>
    </div>
    <div class="livePriceStrip">
      <span>${label("قیمت زنده", "Live")}: <b>${live.price ?? "-"}</b> ${live.quote_asset || ""}</span>
      <span>${label("منبع", "Source")}: ${live.source || live.exchange || "-"}</span>
      <span>${label("بروزرسانی", "Updated")}: ${liveTime}</span>
      <span>${label("اختلاف با کندل", "Delta vs candle")}: ${live.delta_from_candle_percent ?? 0}%</span>
    </div>
    <ul>${reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>
    <div class="reasonMetrics">
      <span>RSI: ${indicators.rsi ?? "-"}</span>
      <span>${label("روند", "Trend")}: ${indicators.trend ?? "-"}</span>
      <span>SL: ${levels.stop_loss ?? "-"}</span>
      <span>TP: ${levels.take_profit ?? "-"}</span>
    </div>
  `;
}

async function refreshReasonsForSymbol(symbol, timeframe) {
  try {
    const data = await api(`/market/analyze/Binance/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(timeframe)}`);
    renderReasonsFromAnalysis(data);
    const target = document.getElementById("feedbackTarget");
    if (target) target.textContent = symbol;
  } catch (error) {
    const reasonsBox = document.getElementById("reasonsBox");
    if (reasonsBox) reasonsBox.textContent = error.message;
  }
}

async function saveComment() {
  try {
    const input = document.getElementById("commentInput");
    const content = input.value.trim();
    if (!content) return;
    const target = activeFeedbackTarget();
    await api("/comments", {
      method: "POST",
      body: JSON.stringify({
        ...target,
        content,
        language: currentLanguage(),
      }),
    });
    input.value = "";
    toast(t("saved"));
    await loadComments();
  } catch (error) {
    toast(error.message);
  }
}

async function loadComments() {
  try {
    const target = activeFeedbackTarget();
    const query = new URLSearchParams(target).toString();
    const comments = await api(`/comments?${query}`);
    const box = document.getElementById("commentsBox");
    if (!comments.length) {
      box.textContent = t("commentsEmpty");
      return;
    }
    box.innerHTML = comments.map((comment) => `
      <article class="commentItem">
        <div>
          <b>${comment.user_email}</b>
          <span>${new Date(comment.created_at).toLocaleString(currentLanguage() === "fa" ? "fa-IR" : "en-US")}</span>
        </div>
        <p>${comment.content}</p>
      </article>
    `).join("");
  } catch (error) {
    toast(error.message);
  }
}

const originalRenderMarketReport = window.renderMarketReport;
if (typeof originalRenderMarketReport === "function") {
  window.renderMarketReport = function patchedRenderMarketReport(report) {
    originalRenderMarketReport(report);
    document.querySelectorAll("#marketReportBox tbody tr").forEach((row, index) => {
      const item = report.items[index];
      if (!item) return;
      row.title = (item.reasons || []).join(" | ");
    });
  };
}

const chartForm = document.getElementById("chartForm");
if (chartForm) {
  chartForm.addEventListener("submit", () => {
    const symbol = document.getElementById("chartSymbol").value.trim().toUpperCase();
    const timeframe = document.getElementById("chartTimeframe").value;
    window.setTimeout(() => refreshReasonsForSymbol(symbol, timeframe), 1200);
  });
}

addLanguageSelector();
addReasonAndFeedbackPanel();
applyLanguage();
