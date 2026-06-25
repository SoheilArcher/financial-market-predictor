let lastAnalysisForSizing = null;
let lastConsensusForSizing = null;

function ensureSocialPanel() {
  if (document.getElementById("socialPanel")) return;
  const analysisPanel = document.getElementById("analysisForm")?.closest(".panel");
  if (!analysisPanel) return;
  const panel = document.createElement("section");
  panel.id = "socialPanel";
  panel.className = "panel";
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
        <button class="primary" type="submit">ذخیره پروفایل</button>
        <div id="myAnalystBox" class="empty">هنوز اطلاعاتی دریافت نشده است.</div>
      </form>
      <form id="portfolioForm" class="socialCard">
        <h2>سرمایه و ریسک</h2>
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
        <button class="primary" type="submit">ذخیره سرمایه</button>
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
    </div>
  `;
  analysisPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadSocialBtn").addEventListener("click", loadSocialDashboard);
  document.getElementById("profileForm").addEventListener("submit", saveAnalystProfile);
  document.getElementById("portfolioForm").addEventListener("submit", savePortfolio);
  document.getElementById("publishLastAnalysisBtn").addEventListener("click", publishLastAnalysis);
  document.getElementById("loadConsensusBtn").addEventListener("click", loadConsensus);
  document.getElementById("calculateSizingBtn").addEventListener("click", calculatePositionSize);
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
  document.getElementById("myAnalystBox").className = "socialStats";
  document.getElementById("myAnalystBox").innerHTML = `
    <span>ID عمومی: <b>${profile.public_id}</b></span>
    <span>دنبال‌کننده: <b>${stats.followers}</b></span>
    <span>دقت: <b>${stats.accuracy}%</b></span>
    <span>امتیاز: <b>${stats.score}</b></span>
  `;
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
    toast("پروفایل تحلیل‌گر ذخیره شد.");
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
    toast("سرمایه و ریسک ذخیره شد.");
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
    toast(`تحلیل منتشر شد: #${data.shared_analysis.id}`);
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
        <span>دنبال‌کننده ${item.stats.followers}</span>
        <span>دقت ${item.stats.accuracy}%</span>
        <span>امتیاز ${item.stats.score}</span>
      </div>
    </div>
  `).join("");
  document.getElementById("topAnalystsBox").className = "analystList";
  document.getElementById("topAnalystsBox").innerHTML = rows || "<div class='empty'>هنوز تحلیل‌گر عمومی وجود ندارد.</div>";
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
        <div><span>نظر غالب</span><b>${data.majority_signal}</b></div>
        <div><span>تحلیل عمومی</span><b>${data.total_public_analyses}</b></div>
        <div><span>برترها</span><b>${data.top_analyst_majority}</b></div>
        <div><span>تعداد برتر</span><b>${data.top_analyst_count}</b></div>
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
        <b>پیشنهاد ورود: ${data.action}</b>
        <span>حجم پوزیشن: ${data.position_value ?? "-"} ${data.currency || ""}</span>
        <span>تعداد واحد: ${data.units ?? "-"}</span>
        <span>ریسک معامله: ${data.risk_amount ?? "-"} ${data.currency || ""}</span>
        <p>${data.reason_fa}</p>
      </div>
    `;
  } catch (error) {
    toast(error.message);
  }
}

ensureSocialPanel();
patchAnalysisForSocial();
