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
  const sessionText = document.getElementById("sessionText");
  if (sessionText && !(window.state && state.token)) sessionText.textContent = t("marketView");
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
}

function addReasonAndFeedbackPanel() {
  if (document.getElementById("feedbackPanel")) return;
  const chartPanel = document.getElementById("chartForm")?.closest(".panel");
  if (!chartPanel) return;

  const panel = document.createElement("section");
  panel.id = "feedbackPanel";
  panel.className = "panel";
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
  reasonsBox.dataset.empty = "0";
  reasonsBox.innerHTML = `
    <div class="reasonHeadline">
      <span class="badge ${(analysis.signal || "wait").toLowerCase()}">${analysis.signal || "-"}</span>
      <b>${analysis.summary_fa || analysis.message || ""}</b>
    </div>
    <ul>${reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>
    <div class="reasonMetrics">
      <span>RSI: ${indicators.rsi ?? "-"}</span>
      <span>Trend: ${indicators.trend ?? "-"}</span>
      <span>SL: ${levels.stop_loss ?? "-"}</span>
      <span>TP: ${levels.take_profit ?? "-"}</span>
    </div>
  `;
}

async function refreshReasonsForSymbol(symbol, timeframe) {
  try {
    const data = await api(`/market/analyze/Binance/${symbol}?timeframe=${encodeURIComponent(timeframe)}`);
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
