let lastAnalysisForSizing = null;
let lastConsensusForSizing = null;

const socialText = {
  fa: {
    title: "تحلیل‌گران، دنبال‌کننده‌ها و مدیریت سرمایه",
    hint: "تحلیل خودت را منتشر کن، اعتبار تحلیل‌گران را ببین و حجم ورود را با سرمایه خودت بسنج.",
    refresh: "بروزرسانی",
    profile: "پروفایل تحلیل‌گر",
    displayName: "نام نمایشی",
    focus: "حوزه بازار",
    bio: "بیوگرافی",
    saveProfile: "ذخیره پروفایل",
    noInfo: "هنوز اطلاعاتی دریافت نشده است.",
    capitalRisk: "سرمایه و ریسک",
    marketType: "نوع بازار",
    capital: "سرمایه",
    currency: "ارز",
    risk: "ریسک هر معامله ٪",
    maxPosition: "حداکثر حجم پوزیشن ٪",
    saveCapital: "ذخیره سرمایه",
    publish: "انتشار آخرین تحلیل من",
    consensus: "نظر تحلیل‌گران روی نماد",
    sizing: "پیشنهاد حجم ورود",
    top: "تحلیل‌گران برتر",
    consensusTitle: "اجماع و پیشنهاد ورود",
    consensusEmpty: "برای دیدن اجماع، نماد را از تحلیل تک‌نماد انتخاب کن.",
    publicId: "ID عمومی",
    followers: "دنبال‌کننده",
    accuracy: "دقت",
    score: "امتیاز",
    savedProfile: "پروفایل تحلیل‌گر ذخیره شد.",
    savedPortfolio: "سرمایه و ریسک ذخیره شد.",
    published: "تحلیل منتشر شد",
    noAnalyst: "هنوز تحلیل‌گر عمومی وجود ندارد.",
    majority: "نظر غالب",
    publicAnalysis: "تحلیل عمومی",
    topAnalysts: "برترها",
    topCount: "تعداد برتر",
    entryAdvice: "پیشنهاد ورود",
    positionValue: "حجم پوزیشن",
    units: "تعداد واحد",
    tradeRisk: "ریسک معامله",
    saved: "ذخیره‌شده",
    edit: "ویرایش",
    cancel: "انصراف",
    followingList: "دنبال‌شده‌ها",
    follow: "دنبال کردن",
    unfollow: "لغو دنبال",
    noFollowing: "هنوز تحلیل‌گری را دنبال نمی‌کنی.",
  },
  en: {
    title: "Analysts, Followers, and Capital Management",
    hint: "Publish your analysis, review analyst credibility, and size entries from your own capital.",
    refresh: "Refresh",
    profile: "Analyst Profile",
    displayName: "Display Name",
    focus: "Market Focus",
    bio: "Bio",
    saveProfile: "Save Profile",
    noInfo: "No data loaded yet.",
    capitalRisk: "Capital and Risk",
    marketType: "Market Type",
    capital: "Capital",
    currency: "Currency",
    risk: "Risk per Trade %",
    maxPosition: "Max Position %",
    saveCapital: "Save Capital",
    publish: "Publish My Latest Analysis",
    consensus: "Analyst Consensus",
    sizing: "Entry Size Suggestion",
    top: "Top Analysts",
    consensusTitle: "Consensus and Entry Suggestion",
    consensusEmpty: "Select a symbol from single-symbol analysis to see consensus.",
    publicId: "Public ID",
    followers: "Followers",
    accuracy: "Accuracy",
    score: "Score",
    savedProfile: "Analyst profile saved.",
    savedPortfolio: "Capital and risk saved.",
    published: "Analysis published",
    noAnalyst: "No public analyst exists yet.",
    majority: "Majority",
    publicAnalysis: "Public Analyses",
    topAnalysts: "Top Analysts",
    topCount: "Top Count",
    entryAdvice: "Entry Suggestion",
    positionValue: "Position Value",
    units: "Units",
    tradeRisk: "Trade Risk",
    saved: "Saved",
    edit: "Edit",
    cancel: "Cancel",
    followingList: "Following",
    follow: "Follow",
    unfollow: "Unfollow",
    noFollowing: "You are not following any analysts yet.",
  },
};

function st(key) {
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  return socialText[lang]?.[key] || socialText.fa[key] || key;
}

function ensureSocialPanel() {
  if (document.getElementById("socialPanel")) return;
  const analysisPanel = document.getElementById("analysisForm")?.closest(".panel");
  if (!analysisPanel) return;
  const panel = document.createElement("section");
  panel.id = "socialPanel";
  panel.className = "panel dashboardBlock";
  panel.dataset.blockId = "social";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>تحلیل‌گران، دنبال‌کننده‌ها و مدیریت سرمایه</h2>
        <p class="hint">تحلیل خودت را منتشر کن، اعتبار تحلیل‌گران را ببین و حجم ورود را با سرمایه خودت بسنج.</p>
      </div>
      <button id="loadSocialBtn" class="ghost" type="button">بروزرسانی</button>
    </div>
    <div class="socialGrid">
      <form id="profileForm" class="socialCard">
        <h2>پروفایل تحلیل‌گر</h2>
        <div id="profileSavedView" class="savedView hidden"></div>
        <div id="profileEditor" class="editorView">
          <label>نام نمایشی<input id="analystName" /></label>
          <label>حوزه بازار
            <select id="marketFocus">
              <option value="crypto">Crypto</option>
              <option value="iran">بورس ایران</option>
              <option value="forex">Forex</option>
              <option value="stocks">Stocks</option>
            </select>
          </label>
          <label>بیوگرافی<textarea id="analystBio" rows="3"></textarea></label>
          <div class="formActions">
            <button class="primary" type="submit">ذخیره پروفایل</button>
            <button id="cancelProfileEditBtn" class="ghost hidden" type="button">انصراف</button>
          </div>
        </div>
        <div id="myAnalystBox" class="empty">هنوز اطلاعاتی دریافت نشده است.</div>
      </form>
      <form id="portfolioForm" class="socialCard">
        <h2>سرمایه و ریسک</h2>
        <div id="portfolioSavedView" class="savedView hidden"></div>
        <div id="portfolioEditor" class="editorView">
          <label>نوع بازار
            <select id="portfolioMarket">
              <option value="crypto">صرافی رمزارز</option>
              <option value="broker">بروکر / فارکس</option>
              <option value="iran">بورس ایران</option>
            </select>
          </label>
          <label>سرمایه<input id="portfolioCapital" type="number" min="0" value="1000" /></label>
          <label>ارز<input id="portfolioCurrency" value="USDT" /></label>
          <label>ریسک هر معامله ٪<input id="portfolioRisk" type="number" min="0.1" max="10" step="0.1" value="1" /></label>
          <label>حداکثر حجم پوزیشن ٪<input id="portfolioMax" type="number" min="1" max="100" step="1" value="20" /></label>
          <div class="formActions">
            <button class="primary" type="submit">ذخیره سرمایه</button>
            <button id="cancelPortfolioEditBtn" class="ghost hidden" type="button">انصراف</button>
          </div>
        </div>
      </form>
    </div>
    <div class="socialActions">
      <button id="publishLastAnalysisBtn" class="ghost" type="button">انتشار آخرین تحلیل من</button>
      <button id="loadConsensusBtn" class="ghost" type="button">نظر تحلیل‌گران روی نماد</button>
      <button id="calculateSizingBtn" class="ghost" type="button">پیشنهاد حجم ورود</button>
    </div>
    <div class="socialGrid">
      <div class="socialCard">
        <h2>تحلیل‌گران برتر</h2>
        <div id="topAnalystsBox" class="empty">هنوز دریافت نشده است.</div>
      </div>
      <div class="socialCard">
        <h2>اجماع و پیشنهاد ورود</h2>
        <div id="consensusBox" class="empty">برای دیدن اجماع، نماد را از تحلیل تک‌نماد انتخاب کن.</div>
      </div>
      <div class="socialCard">
        <h2 id="followingTitle">دنبال‌شده‌ها</h2>
        <div id="followingBox" class="empty">هنوز تحلیل‌گری را دنبال نمی‌کنی.</div>
      </div>
    </div>
  `;
  analysisPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadSocialBtn").addEventListener("click", loadSocialDashboard);
  document.getElementById("profileForm").addEventListener("submit", saveAnalystProfile);
  document.getElementById("portfolioForm").addEventListener("submit", savePortfolio);
  document.getElementById("cancelProfileEditBtn").addEventListener("click", () => setProfileEditing(false));
  document.getElementById("cancelPortfolioEditBtn").addEventListener("click", () => setPortfolioEditing(false));
  panel.addEventListener("click", handleSocialClick);
  document.getElementById("publishLastAnalysisBtn").addEventListener("click", publishLastAnalysis);
  document.getElementById("loadConsensusBtn").addEventListener("click", loadConsensus);
  document.getElementById("calculateSizingBtn").addEventListener("click", calculatePositionSize);
  applySocialLanguage();
  if (window.state?.token || localStorage.getItem("market_ai_token")) {
    loadSocialDashboard();
  }
}

function applySocialLanguage() {
  const panel = document.getElementById("socialPanel");
  if (!panel) return;
  panel.querySelector(".panelHeader h2").textContent = st("title");
  panel.querySelector(".panelHeader .hint").textContent = st("hint");
  document.getElementById("loadSocialBtn").textContent = st("refresh");
  const cards = panel.querySelectorAll(".socialCard");
  if (cards[0]) cards[0].querySelector("h2").textContent = st("profile");
  if (cards[1]) cards[1].querySelector("h2").textContent = st("capitalRisk");
  const labels = [
    ["analystName", "displayName"],
    ["marketFocus", "focus"],
    ["analystBio", "bio"],
    ["portfolioMarket", "marketType"],
    ["portfolioCapital", "capital"],
    ["portfolioCurrency", "currency"],
    ["portfolioRisk", "risk"],
    ["portfolioMax", "maxPosition"],
  ];
  labels.forEach(([id, key]) => {
    const label = panel.querySelector(`label:has(#${id})`);
    if (label?.firstChild) label.firstChild.textContent = `${st(key)}\n`;
  });
  document.querySelector("#profileForm button").textContent = st("saveProfile");
  document.querySelector("#portfolioForm button").textContent = st("saveCapital");
  document.getElementById("publishLastAnalysisBtn").textContent = st("publish");
  document.getElementById("loadConsensusBtn").textContent = st("consensus");
  document.getElementById("calculateSizingBtn").textContent = st("sizing");
  const headings = panel.querySelectorAll(".socialGrid .socialCard h2");
  if (headings[2]) headings[2].textContent = st("top");
  if (headings[3]) headings[3].textContent = st("consensusTitle");
  if (headings[4]) headings[4].textContent = st("followingList");
  const consensusBox = document.getElementById("consensusBox");
  if (consensusBox?.className === "empty") consensusBox.textContent = st("consensusEmpty");
  const topBox = document.getElementById("topAnalystsBox");
  if (topBox?.className === "empty") topBox.textContent = st("noInfo");
  const followingBox = document.getElementById("followingBox");
  if (followingBox?.className === "empty") followingBox.textContent = st("noFollowing");
  document.getElementById("cancelProfileEditBtn").textContent = st("cancel");
  document.getElementById("cancelPortfolioEditBtn").textContent = st("cancel");
}

function patchAnalysisForSocial() {
  const form = document.getElementById("analysisForm");
  if (!form || form.dataset.socialPatched) return;
  form.dataset.socialPatched = "1";
  form.addEventListener("submit", () => {
    window.setTimeout(() => {
      try {
        const result = JSON.parse(document.getElementById("analysisResult").textContent);
        if (result && result.signal) lastAnalysisForSizing = result;
      } catch {
        // JSON is not ready or the request failed.
      }
    }, 1200);
  });
}

async function loadSocialDashboard() {
  try {
    const data = await api("/social/me");
    renderMySocial(data);
    await loadTopAnalysts();
  } catch (error) {
    document.getElementById("myAnalystBox").textContent = error.message;
  }
}

function renderMySocial(data) {
  const profile = data.profile || {};
  const stats = data.stats || {};
  const portfolio = data.portfolio || {};
  document.getElementById("analystName").value = profile.display_name || "";
  document.getElementById("analystBio").value = profile.bio || "";
  document.getElementById("marketFocus").value = profile.market_focus || "crypto";
  document.getElementById("portfolioMarket").value = portfolio.market_type || "crypto";
  document.getElementById("portfolioCapital").value = portfolio.capital ?? 1000;
  document.getElementById("portfolioCurrency").value = portfolio.currency || "USDT";
  document.getElementById("portfolioRisk").value = portfolio.risk_percent ?? 1;
  document.getElementById("portfolioMax").value = portfolio.max_position_percent ?? 20;
  renderSavedProfile(profile);
  renderSavedPortfolio(portfolio);
  renderFollowing(data.following || []);
  setProfileEditing(false);
  setPortfolioEditing(false);
  document.getElementById("myAnalystBox").className = "socialStats";
  document.getElementById("myAnalystBox").innerHTML = `
    <span>${st("publicId")}: <b>${profile.public_id}</b></span>
    <span>${st("followers")}: <b>${stats.followers}</b></span>
    <span>${st("accuracy")}: <b>${stats.accuracy}%</b></span>
    <span>${st("score")}: <b>${stats.score}</b></span>
  `;
}

function setProfileEditing(isEditing) {
  document.getElementById("profileEditor").classList.toggle("hidden", !isEditing);
  document.getElementById("profileSavedView").classList.toggle("hidden", isEditing);
  document.getElementById("cancelProfileEditBtn").classList.toggle("hidden", !isEditing);
}

function setPortfolioEditing(isEditing) {
  document.getElementById("portfolioEditor").classList.toggle("hidden", !isEditing);
  document.getElementById("portfolioSavedView").classList.toggle("hidden", isEditing);
  document.getElementById("cancelPortfolioEditBtn").classList.toggle("hidden", !isEditing);
}

function renderSavedProfile(profile) {
  const box = document.getElementById("profileSavedView");
  box.innerHTML = `
    <div class="savedHeader"><b>${st("saved")}</b><button class="ghost" type="button" data-social-edit="profile">${st("edit")}</button></div>
    <div class="savedGrid">
      <span>${st("displayName")}: <b>${profile.display_name || "-"}</b></span>
      <span>${st("focus")}: <b>${profile.market_focus || "-"}</b></span>
      <span>${st("publicId")}: <b>${profile.public_id || "-"}</b></span>
    </div>
    <p>${profile.bio || "-"}</p>
  `;
}

function renderSavedPortfolio(portfolio) {
  const box = document.getElementById("portfolioSavedView");
  box.innerHTML = `
    <div class="savedHeader"><b>${st("saved")}</b><button class="ghost" type="button" data-social-edit="portfolio">${st("edit")}</button></div>
    <div class="savedGrid">
      <span>${st("marketType")}: <b>${portfolio.market_type || "-"}</b></span>
      <span>${st("capital")}: <b>${portfolio.capital ?? "-"} ${portfolio.currency || ""}</b></span>
      <span>${st("risk")}: <b>${portfolio.risk_percent ?? "-"}%</b></span>
      <span>${st("maxPosition")}: <b>${portfolio.max_position_percent ?? "-"}%</b></span>
    </div>
  `;
}

function renderFollowing(items) {
  const box = document.getElementById("followingBox");
  box.className = "analystList";
  box.innerHTML = (items || []).map((item) => `
    <div class="analystRow">
      <div>
        <b>${item.profile.display_name}</b>
        <span>${item.profile.public_id}</span>
      </div>
      <div class="socialStats compact">
        <span>${st("followers")} ${item.stats.followers}</span>
        <span>${st("accuracy")} ${item.stats.accuracy}%</span>
      </div>
    </div>
  `).join("") || `<div class='empty'>${st("noFollowing")}</div>`;
}

async function handleSocialClick(event) {
  const editButton = event.target.closest("[data-social-edit]");
  if (editButton?.dataset.socialEdit === "profile") setProfileEditing(true);
  if (editButton?.dataset.socialEdit === "portfolio") setPortfolioEditing(true);

  const followButton = event.target.closest("[data-follow-analyst]");
  if (!followButton) return;
  const userId = followButton.dataset.followAnalyst;
  const following = followButton.dataset.following === "true";
  try {
    followButton.disabled = true;
    await api(`/social/analysts/${userId}/follow`, { method: following ? "DELETE" : "POST" });
    await loadSocialDashboard();
  } catch (error) {
    toast(error.message);
  } finally {
    followButton.disabled = false;
  }
}

async function saveAnalystProfile(event) {
  event.preventDefault();
  try {
    await api("/social/profile", {
      method: "PUT",
      body: JSON.stringify({
        display_name: document.getElementById("analystName").value.trim(),
        bio: document.getElementById("analystBio").value.trim(),
        market_focus: document.getElementById("marketFocus").value,
        is_public: true,
      }),
    });
    toast(st("savedProfile"));
    await loadSocialDashboard();
  } catch (error) {
    toast(error.message);
  }
}

async function savePortfolio(event) {
  event.preventDefault();
  try {
    await api("/social/portfolio", {
      method: "PUT",
      body: JSON.stringify({
        market_type: document.getElementById("portfolioMarket").value,
        capital: Number(document.getElementById("portfolioCapital").value || 0),
        currency: document.getElementById("portfolioCurrency").value.trim() || "USDT",
        risk_percent: Number(document.getElementById("portfolioRisk").value || 1),
        max_position_percent: Number(document.getElementById("portfolioMax").value || 20),
      }),
    });
    toast(st("savedPortfolio"));
    await loadSocialDashboard();
  } catch (error) {
    toast(error.message);
  }
}

async function publishLastAnalysis() {
  try {
    const payload = {
      signal_record_id: lastAnalysisForSizing?.signal_record_id || null,
      title: lastAnalysisForSizing ? `${lastAnalysisForSizing.symbol} ${lastAnalysisForSizing.signal}` : "تحلیل جدید",
      note: lastAnalysisForSizing?.summary_fa || "",
    };
    const data = await api("/social/publish", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    toast(`${st("published")}: #${data.shared_analysis.id}`);
    await loadConsensus();
  } catch (error) {
    toast(error.message);
  }
}

async function loadTopAnalysts() {
  const data = await api("/social/analysts/top?days=30&limit=10");
  const rows = (data.items || []).map((item) => `
    <div class="analystRow">
      <div>
        <b>${item.profile.display_name}</b>
        <span>${item.profile.public_id}</span>
      </div>
      <div class="socialStats compact">
        <span>${st("followers")} ${item.stats.followers}</span>
        <span>${st("accuracy")} ${item.stats.accuracy}%</span>
        <span>${st("score")} ${item.stats.score}</span>
      </div>
      ${item.is_me ? "" : `<button class="ghost" type="button" data-follow-analyst="${item.profile.user_id}" data-following="${item.following ? "true" : "false"}">${item.following ? st("unfollow") : st("follow")}</button>`}
    </div>
  `).join("");
  document.getElementById("topAnalystsBox").className = "analystList";
  document.getElementById("topAnalystsBox").innerHTML = rows || `<div class='empty'>${st("noAnalyst")}</div>`;
}

async function loadConsensus() {
  try {
    const symbol = (document.getElementById("symbol").value || "BTCUSDT").trim().toUpperCase();
    const timeframe = document.getElementById("timeframe").value;
    const data = await api(`/social/consensus?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&days=30`);
    lastConsensusForSizing = data;
    document.getElementById("consensusBox").className = "reportBox";
    document.getElementById("consensusBox").innerHTML = `
      <div class="summaryGrid">
        <div><span>${st("majority")}</span><b>${data.majority_signal}</b></div>
        <div><span>${st("publicAnalysis")}</span><b>${data.total_public_analyses}</b></div>
        <div><span>${st("topAnalysts")}</span><b>${data.top_analyst_majority}</b></div>
        <div><span>${st("topCount")}</span><b>${data.top_analyst_count}</b></div>
      </div>
      <p class="reportSummary">${data.summary_fa}</p>
    `;
  } catch (error) {
    document.getElementById("consensusBox").className = "empty";
    document.getElementById("consensusBox").textContent = error.message;
  }
}

async function calculatePositionSize() {
  try {
    let signal = lastAnalysisForSizing;
    if (!signal) {
      signal = JSON.parse(document.getElementById("analysisResult").textContent);
    }
    const data = await api("/social/position-size", {
      method: "POST",
      body: JSON.stringify({ signal, consensus: lastConsensusForSizing }),
    });
    document.getElementById("consensusBox").className = "reportBox";
    document.getElementById("consensusBox").innerHTML += `
      <div class="positionAdvice">
        <b>${st("entryAdvice")}: ${data.action}</b>
        <span>${st("positionValue")}: ${data.position_value ?? "-"} ${data.currency || ""}</span>
        <span>${st("units")}: ${data.units ?? "-"}</span>
        <span>${st("tradeRisk")}: ${data.risk_amount ?? "-"} ${data.currency || ""}</span>
        <p>${data.reason_fa}</p>
      </div>
    `;
  } catch (error) {
    toast(error.message);
  }
}

ensureSocialPanel();
patchAnalysisForSocial();
window.addEventListener("market-ai-language-change", applySocialLanguage);
