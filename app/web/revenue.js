const revenueText = {
  fa: {
    title: "تقسیم درآمد و پرداخت مشارکت‌کننده‌ها",
    hint: "درآمد خالص بعد از هزینه‌های سیستم بین مالک و کاربران منتخب تقسیم می‌شود.",
    refresh: "بروزرسانی",
    rule: "قانون تقسیم",
    owner: "سهم مالک ٪",
    contributors: "سهم مشارکت‌کننده‌ها ٪",
    currency: "ارز",
    saveRule: "ذخیره قانون",
    contributor: "افزودن مشارکت‌کننده",
    userId: "شناسه کاربر",
    weight: "وزن دستی",
    role: "نقش",
    payoutMethod: "روش پرداخت",
    payoutAccount: "حساب پرداخت",
    saveContributor: "افزودن / بروزرسانی",
    pool: "صندوق درآمد دوره",
    period: "دوره",
    gross: "درآمد کل",
    costs: "هزینه سیستم",
    note: "یادداشت",
    createPool: "محاسبه صندوق",
    selected: "کاربران منتخب",
    payouts: "پرداخت‌ها",
    score: "امتیاز",
    amount: "مبلغ",
    status: "وضعیت",
    markPaid: "پرداخت شد",
    noData: "هنوز داده‌ای وجود ندارد.",
    saved: "ذخیره شد.",
  },
  en: {
    title: "Revenue Sharing and Contributor Payouts",
    hint: "Net revenue after system costs is split between the owner and selected contributors.",
    refresh: "Refresh",
    rule: "Split Rule",
    owner: "Owner %",
    contributors: "Contributors %",
    currency: "Currency",
    saveRule: "Save Rule",
    contributor: "Add Contributor",
    userId: "User ID",
    weight: "Manual Weight",
    role: "Role",
    payoutMethod: "Payout Method",
    payoutAccount: "Payout Account",
    saveContributor: "Add / Update",
    pool: "Revenue Pool",
    period: "Period",
    gross: "Gross Revenue",
    costs: "System Costs",
    note: "Note",
    createPool: "Calculate Pool",
    selected: "Selected Users",
    payouts: "Payouts",
    score: "Score",
    amount: "Amount",
    status: "Status",
    markPaid: "Mark Paid",
    noData: "No data yet.",
    saved: "Saved.",
  },
};

let lastRevenuePool = null;

function rt(key) {
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  return revenueText[lang]?.[key] || revenueText.fa[key] || key;
}

function ensureRevenuePanel() {
  if (document.getElementById("revenuePanel")) return;
  const adminPanel = document.getElementById("adminPanel");
  if (!adminPanel) return;
  const panel = document.createElement("section");
  panel.id = "revenuePanel";
  panel.className = "panel hidden";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>${rt("title")}</h2>
        <p class="hint">${rt("hint")}</p>
      </div>
      <button id="loadRevenueBtn" class="ghost" type="button">${rt("refresh")}</button>
    </div>
    <div class="revenueGrid">
      <form id="revenueRuleForm" class="revenueCard">
        <h2>${rt("rule")}</h2>
        <label>${rt("owner")}<input id="ownerPercent" type="number" min="0" max="100" step="1" value="50" /></label>
        <label>${rt("contributors")}<input id="contributorPercent" type="number" min="0" max="100" step="1" value="50" /></label>
        <label>${rt("currency")}<input id="revenueCurrency" value="USD" /></label>
        <button class="primary" type="submit">${rt("saveRule")}</button>
      </form>
      <form id="revenueContributorForm" class="revenueCard">
        <h2>${rt("contributor")}</h2>
        <label>${rt("userId")}<input id="revenueUserId" type="number" min="1" /></label>
        <label>${rt("weight")}<input id="revenueWeight" type="number" min="0" step="0.1" value="1" /></label>
        <label>${rt("role")}<input id="revenueRole" value="analyst" /></label>
        <label>${rt("payoutMethod")}<input id="revenuePayoutMethod" value="manual" /></label>
        <label>${rt("payoutAccount")}<input id="revenuePayoutAccount" /></label>
        <button class="primary" type="submit">${rt("saveContributor")}</button>
      </form>
      <form id="revenuePoolForm" class="revenueCard">
        <h2>${rt("pool")}</h2>
        <label>${rt("period")}<input id="revenuePeriod" value="${new Date().toISOString().slice(0, 7)}" /></label>
        <label>${rt("gross")}<input id="grossRevenue" type="number" min="0" step="0.01" value="1000" /></label>
        <label>${rt("costs")}<input id="systemCosts" type="number" min="0" step="0.01" value="0" /></label>
        <label>${rt("note")}<input id="revenueNote" /></label>
        <button class="primary" type="submit">${rt("createPool")}</button>
      </form>
    </div>
    <div class="revenueGrid">
      <div class="revenueCard">
        <h2>${rt("selected")}</h2>
        <div id="revenueContributorsBox" class="empty">${rt("noData")}</div>
      </div>
      <div class="revenueCard">
        <h2>${rt("payouts")}</h2>
        <div id="revenuePayoutsBox" class="empty">${rt("noData")}</div>
      </div>
    </div>
  `;
  adminPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("loadRevenueBtn").addEventListener("click", loadRevenueDashboard);
  document.getElementById("revenueRuleForm").addEventListener("submit", saveRevenueRule);
  document.getElementById("revenueContributorForm").addEventListener("submit", saveRevenueContributor);
  document.getElementById("revenuePoolForm").addEventListener("submit", createRevenuePool);
}

function syncRevenueVisibility() {
  const panel = document.getElementById("revenuePanel");
  if (!panel) return;
  panel.classList.toggle("hidden", !(window.state?.user?.role === "admin"));
}

async function loadRevenueDashboard() {
  syncRevenueVisibility();
  if (window.state?.user?.role !== "admin") return;
  const [rule, contributors, pools] = await Promise.all([
    api("/admin/revenue/rule"),
    api("/admin/revenue/contributors"),
    api("/admin/revenue/pools"),
  ]);
  document.getElementById("ownerPercent").value = rule.owner_percent;
  document.getElementById("contributorPercent").value = rule.contributor_percent;
  document.getElementById("revenueCurrency").value = rule.currency;
  renderRevenueContributors(contributors.items || []);
  if ((pools.items || []).length) {
    const detail = await api(`/admin/revenue/pools/${pools.items[0].id}`);
    renderRevenuePayouts(detail);
  }
}

function renderRevenueContributors(items) {
  if (!items.length) {
    document.getElementById("revenueContributorsBox").className = "empty";
    document.getElementById("revenueContributorsBox").textContent = rt("noData");
    return;
  }
  document.getElementById("revenueContributorsBox").className = "tableWrap";
  document.getElementById("revenueContributorsBox").innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Email</th><th>${rt("role")}</th><th>${rt("weight")}</th><th>${rt("score")}</th><th>Followers</th></tr></thead>
      <tbody>${items.map((item) => `
        <tr>
          <td>${item.user_id}</td>
          <td>${item.email || "-"}</td>
          <td>${item.role_label || "-"}</td>
          <td>${item.manual_weight}</td>
          <td>${item.score?.score ?? 0}</td>
          <td>${item.score?.followers ?? 0}</td>
        </tr>
      `).join("")}</tbody>
    </table>
  `;
}

function renderRevenuePayouts(detail) {
  lastRevenuePool = detail;
  const payouts = detail.payouts || [];
  if (!payouts.length) {
    document.getElementById("revenuePayoutsBox").className = "empty";
    document.getElementById("revenuePayoutsBox").textContent = rt("noData");
    return;
  }
  document.getElementById("revenuePayoutsBox").className = "tableWrap";
  document.getElementById("revenuePayoutsBox").innerHTML = `
    <div class="summaryGrid">
      <div><span>Net</span><b>${detail.pool.net_revenue} ${detail.pool.currency}</b></div>
      <div><span>Owner</span><b>${detail.pool.owner_percent}%</b></div>
      <div><span>Contributors</span><b>${detail.pool.contributor_percent}%</b></div>
    </div>
    <table>
      <thead><tr><th>User</th><th>Type</th><th>${rt("score")}</th><th>${rt("amount")}</th><th>${rt("status")}</th><th></th></tr></thead>
      <tbody>${payouts.map((item) => `
        <tr>
          <td>${item.email || item.full_name || "-"}</td>
          <td>${item.payout_type}</td>
          <td>${item.score}</td>
          <td>${item.amount} ${item.currency}</td>
          <td>${item.status}</td>
          <td>${item.status === "pending" && item.payout_type !== "owner" ? `<button class="ghost" type="button" data-payout-id="${item.id}">${rt("markPaid")}</button>` : ""}</td>
        </tr>
      `).join("")}</tbody>
    </table>
  `;
  document.querySelectorAll("[data-payout-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/admin/revenue/payouts/${button.dataset.payoutId}/paid`, { method: "POST" });
      if (lastRevenuePool) {
        const detail = await api(`/admin/revenue/pools/${lastRevenuePool.pool.id}`);
        renderRevenuePayouts(detail);
      }
    });
  });
}

async function saveRevenueRule(event) {
  event.preventDefault();
  await api("/admin/revenue/rule", {
    method: "PUT",
    body: JSON.stringify({
      owner_percent: Number(document.getElementById("ownerPercent").value || 0),
      contributor_percent: Number(document.getElementById("contributorPercent").value || 0),
      currency: document.getElementById("revenueCurrency").value || "USD",
    }),
  });
  toast(rt("saved"));
  await loadRevenueDashboard();
}

async function saveRevenueContributor(event) {
  event.preventDefault();
  await api("/admin/revenue/contributors", {
    method: "POST",
    body: JSON.stringify({
      user_id: Number(document.getElementById("revenueUserId").value),
      manual_weight: Number(document.getElementById("revenueWeight").value || 1),
      role_label: document.getElementById("revenueRole").value,
      payout_method: document.getElementById("revenuePayoutMethod").value,
      payout_account: document.getElementById("revenuePayoutAccount").value,
      status: "active",
    }),
  });
  toast(rt("saved"));
  await loadRevenueDashboard();
}

async function createRevenuePool(event) {
  event.preventDefault();
  const detail = await api("/admin/revenue/pools", {
    method: "POST",
    body: JSON.stringify({
      period: document.getElementById("revenuePeriod").value,
      gross_revenue: Number(document.getElementById("grossRevenue").value || 0),
      system_costs: Number(document.getElementById("systemCosts").value || 0),
      note: document.getElementById("revenueNote").value,
    }),
  });
  renderRevenuePayouts(detail);
  toast(rt("saved"));
}

ensureRevenuePanel();
syncRevenueVisibility();
window.addEventListener("market-ai-language-change", () => {
  const oldPanel = document.getElementById("revenuePanel");
  if (oldPanel) oldPanel.remove();
  ensureRevenuePanel();
  syncRevenueVisibility();
  if (window.state?.user?.role === "admin") loadRevenueDashboard().catch(() => {});
});
