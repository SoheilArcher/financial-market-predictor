const state = {
  token: localStorage.getItem("market_ai_token") || "",
  user: JSON.parse(localStorage.getItem("market_ai_user") || "null"),
  authMode: "login",
};

const $ = (id) => document.getElementById(id);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  window.setTimeout(() => el.classList.add("hidden"), 3200);
}

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail || data);
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return data;
}

function setSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("market_ai_token", token);
  localStorage.setItem("market_ai_user", JSON.stringify(user));
  renderSession();
}

function clearSession() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("market_ai_token");
  localStorage.removeItem("market_ai_user");
  $("analysisResult").textContent = "خروجی تحلیل اینجا نمایش داده می‌شود.";
  $("marketReportBox").textContent = "گزارش کلی بازار اینجا نمایش داده می‌شود.";
  $("marketReportBox").className = "empty";
  renderSession();
}

function renderSession() {
  const isLoggedIn = Boolean(state.token && state.user);
  $("logoutBtn").classList.toggle("hidden", !isLoggedIn);
  $("authForm").classList.toggle("hidden", isLoggedIn);
  $("accountPanel").classList.toggle("hidden", !isLoggedIn);
  $("adminPanel").classList.toggle("hidden", !isLoggedIn || state.user?.role !== "admin");
  $("sessionText").textContent = isLoggedIn
    ? "وارد حساب شدید. حالا می‌توانید اشتراک، تحلیل‌ها و گزارش بازار را مدیریت کنید."
    : "برای تست محصول وارد حساب شوید یا ثبت‌نام کنید.";

  if (isLoggedIn) {
    $("accountEmail").textContent = state.user.email;
    $("accountStatus").textContent = state.user.status;
    $("accountCountry").textContent = state.user.country || "-";
    $("roleBadge").textContent = state.user.role;
    $("roleBadge").className = `badge ${state.user.role}`;
    $("email").value = "";
    $("password").value = "";
    $("fullName").value = "";
  } else {
    $("meBox").textContent = "هنوز وارد نشده‌اید.";
    $("accountEmail").textContent = "-";
    $("accountStatus").textContent = "-";
    $("accountCountry").textContent = "-";
    $("roleBadge").textContent = "";
    $("roleBadge").className = "badge";
  }
  if (typeof syncRevenueVisibility === "function") {
    syncRevenueVisibility();
  }
}

function renderJson(target, data) {
  target.textContent = JSON.stringify(data, null, 2);
}

async function refreshMe() {
  if (!state.token) return;
  const user = await api("/auth/me");
  state.user = user;
  localStorage.setItem("market_ai_user", JSON.stringify(user));
  const sub = await api("/subscription/me");
  $("meBox").innerHTML = sub
    ? `پلن فعال: <b>${sub.plan.code}</b><br>مصرف امروز: ${sub.usage_today.used} از ${sub.usage_today.limit}<br>پایان: ${new Date(sub.ends_at).toLocaleString("fa-IR")}`
    : "اشتراک فعال ندارید.";
  renderSession();
}

function renderUsers(users) {
  if (!users.length) {
    $("adminBox").innerHTML = '<div class="empty">کاربری وجود ندارد.</div>';
    return;
  }
  const rows = users.map((user) => `
    <tr>
      <td>${user.id}</td>
      <td>${user.email}</td>
      <td><span class="badge ${user.role}">${user.role}</span></td>
      <td><span class="badge ${user.status}">${user.status}</span></td>
      <td>${user.subscription ? user.subscription.plan.code : "-"}</td>
      <td>${user.subscription ? new Date(user.subscription.ends_at).toLocaleDateString("fa-IR") : "-"}</td>
    </tr>
  `).join("");
  $("adminBox").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>ایمیل</th>
          <th>نقش</th>
          <th>وضعیت</th>
          <th>پلن</th>
          <th>پایان اشتراک</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderAdminManagedRequests(data) {
  const rows = (data.items || []).map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${item.user_id}</td>
      <td>${item.capital_amount} ${item.capital_currency}</td>
      <td>${item.preferred_market}</td>
      <td><span class="badge ${item.status}">${item.status}</span></td>
      <td>${item.latest_report?.net_yearly_profit ?? "-"}</td>
      <td>${item.latest_report?.net_return_percent ?? "-"}%</td>
      <td>${item.notes || "-"}</td>
      <td>
        <div class="reportActions">
          <button class="ghost" data-managed-status="approved" data-id="${item.id}" type="button">Approve</button>
          <button class="ghost" data-managed-status="active" data-id="${item.id}" type="button">Active</button>
          <button class="ghost" data-managed-status="rejected" data-id="${item.id}" type="button">Reject</button>
          <button class="ghost" data-managed-status="settled" data-id="${item.id}" type="button">Settle</button>
        </div>
      </td>
    </tr>
  `).join("");
  $("adminFinanceBox").innerHTML = `
    <h3>درخواست‌های درآمد ثابت ایران</h3>
    <table>
      <thead><tr><th>ID</th><th>User</th><th>سرمایه</th><th>بازار</th><th>وضعیت</th><th>سود خالص</th><th>بازده</th><th>یادداشت</th><th>اقدام</th></tr></thead>
      <tbody>${rows || "<tr><td colspan='9'>درخواستی نیست.</td></tr>"}</tbody>
    </table>
  `;
}

function renderAdminInvoices(data) {
  const rows = (data.items || []).map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${item.user_id}</td>
      <td>${item.managed_request_id || "-"}</td>
      <td>${item.amount} ${item.currency}</td>
      <td>${item.network}</td>
      <td><span class="badge ${item.status}">${item.status}</span></td>
      <td><code>${item.tx_hash || "-"}</code></td>
      <td>${item.payer_wallet || "-"}</td>
      <td>
        <div class="reportActions">
          <button class="ghost" data-invoice-status="confirmed" data-id="${item.id}" type="button">Confirm</button>
          <button class="ghost" data-invoice-status="rejected" data-id="${item.id}" type="button">Reject</button>
          <button class="ghost" data-invoice-status="refunded" data-id="${item.id}" type="button">Refund</button>
        </div>
      </td>
    </tr>
  `).join("");
  $("adminFinanceBox").innerHTML = `
    <h3>پرداخت‌های کریپتو</h3>
    <table>
      <thead><tr><th>ID</th><th>User</th><th>Req</th><th>مبلغ</th><th>شبکه</th><th>وضعیت</th><th>Tx</th><th>Wallet</th><th>اقدام</th></tr></thead>
      <tbody>${rows || "<tr><td colspan='9'>پرداختی نیست.</td></tr>"}</tbody>
    </table>
  `;
}

function renderMarketReport(report) {
  const summary = report.summary;
  const label = (fa, en) => (typeof currentLanguage === "function" && currentLanguage() === "en" ? en : fa);
  const rows = report.items.map((item) => `
    <tr>
      <td>${item.symbol}</td>
      <td>${item.live_price?.price ?? item.price ?? "-"}</td>
      <td><span class="badge ${item.signal.toLowerCase()}">${item.signal}</span></td>
      <td>${item.confidence ?? 0}</td>
      <td>${item.change_percent ?? 0}%</td>
      <td>${item.indicators ? item.indicators.rsi : "-"}</td>
      <td>${item.indicators ? item.indicators.trend : "-"}</td>
      <td>${item.risk || "-"}</td>
      <td>
        <div class="reportActions">
          <button class="ghost" type="button" data-report-action="chart" data-symbol="${item.symbol}">${label("چارت", "Chart")}</button>
          <button class="ghost" type="button" data-report-action="plan" data-symbol="${item.symbol}">${label("پلن", "Plan")}</button>
        </div>
      </td>
    </tr>
  `).join("");
  $("marketReportBox").className = "reportBox";
  $("marketReportBox").innerHTML = `
    <div class="summaryGrid">
      <div><span>${label("جهت کلی", "Market Bias")}</span><b>${summary.market_bias}</b></div>
      <div><span>LONG</span><b>${summary.long_count}</b></div>
      <div><span>SHORT</span><b>${summary.short_count}</b></div>
      <div><span>WAIT</span><b>${summary.wait_count}</b></div>
      <div><span>${label("میانگین تغییر", "Average Change")}</span><b>${summary.average_change_percent}%</b></div>
      <div><span>${label("مصرف امروز", "Today Usage")}</span><b>${report.subscription.daily_used}/${report.subscription.daily_limit}</b></div>
    </div>
    <p class="reportSummary">${summary.summary_fa}</p>
    <div class="tableWrap">
      <table>
        <thead>
          <tr>
            <th>${label("نماد", "Symbol")}</th>
            <th>${label("قیمت زنده", "Live Price")}</th>
            <th>${label("سیگنال", "Signal")}</th>
            <th>${label("اعتماد", "Confidence")}</th>
            <th>${label("تغییر", "Change")}</th>
            <th>RSI</th>
            <th>${label("روند", "Trend")}</th>
            <th>${label("ریسک", "Risk")}</th>
            <th>${label("اقدام سریع", "Quick Action")}</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

async function openReportSymbol(symbol, action) {
  const timeframe = $("reportTimeframe").value;
  if (action === "chart") {
    $("chartSymbol").value = symbol;
    $("chartTimeframe").value = timeframe;
    document.querySelector('[data-block-id="chart"]')?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (typeof loadChart === "function") {
      await loadChart();
    }
    return;
  }
  if (action === "plan") {
    if (typeof window.ensureTradePanel === "function") {
      window.ensureTradePanel();
    }
    $("tradeSymbol").value = symbol;
    $("tradeTimeframe").value = timeframe;
    $("tradeEntryPrice").value = "";
    $("tradeSide").value = "";
    document.getElementById("tradePlanPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (typeof window.loadTradePlan === "function") {
      await window.loadTradePlan();
    }
  }
}

async function loadAdmin() {
  const users = await api("/admin/users");
  renderUsers(users);
}

async function loadManagedAdmin() {
  const status = $("adminRequestStatus").value;
  const query = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  renderAdminManagedRequests(await api(`/admin/managed-requests${query}`));
}

async function loadInvoicesAdmin() {
  const status = $("adminInvoiceStatus").value;
  const query = status ? `?status_filter=${encodeURIComponent(status)}` : "";
  renderAdminInvoices(await api(`/admin/crypto-invoices${query}`));
}

async function updateManagedStatus(id, status) {
  await api(`/admin/managed-requests/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  await loadManagedAdmin();
  toast("وضعیت درخواست بروزرسانی شد.");
}

async function updateInvoiceStatus(id, status) {
  await api(`/admin/crypto-invoices/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  await loadInvoicesAdmin();
  toast("وضعیت پرداخت بروزرسانی شد.");
}

$("marketReportBox").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-report-action]");
  if (!button) return;
  try {
    button.disabled = true;
    await openReportSymbol(button.dataset.symbol, button.dataset.reportAction);
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
});

$("adminFinanceBox").addEventListener("click", async (event) => {
  const managedButton = event.target.closest("[data-managed-status]");
  const invoiceButton = event.target.closest("[data-invoice-status]");
  try {
    if (managedButton) {
      managedButton.disabled = true;
      await updateManagedStatus(managedButton.dataset.id, managedButton.dataset.managedStatus);
    }
    if (invoiceButton) {
      invoiceButton.disabled = true;
      await updateInvoiceStatus(invoiceButton.dataset.id, invoiceButton.dataset.invoiceStatus);
    }
  } catch (error) {
    toast(error.message);
  } finally {
    if (managedButton) managedButton.disabled = false;
    if (invoiceButton) invoiceButton.disabled = false;
  }
});

document.querySelectorAll("[data-auth-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    state.authMode = button.dataset.authMode;
    document.querySelectorAll("[data-auth-mode]").forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    $("nameField").classList.toggle("hidden", state.authMode !== "register");
    $("countryField").classList.toggle("hidden", state.authMode !== "register");
  });
});

$("authForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = {
      email: $("email").value.trim(),
      password: $("password").value,
    };
    if (state.authMode === "register") {
      payload.full_name = $("fullName").value.trim() || null;
      payload.country = $("country").value || null;
    }
    const data = await api(`/auth/${state.authMode}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (state.authMode === "register" && data.user?.status === "pending_email") {
      $("resendVerificationBtn").classList.remove("hidden");
      toast("ثبت‌نام انجام شد. لینک تایید ایمیل را باز کنید.");
      return;
    }
    setSession(data.access_token, data.user);
    await refreshMe();
    toast("ورود موفق بود.");
  } catch (error) {
    toast(error.message);
  }
});

$("resendVerificationBtn").addEventListener("click", async () => {
  try {
    const email = $("email").value.trim();
    if (!email) {
      toast("ایمیل را وارد کنید.");
      return;
    }
    await api("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    toast("اگر ایمیل درست باشد، لینک تایید ارسال شد.");
  } catch (error) {
    toast(error.message);
  }
});

$("analysisForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const exchange = $("exchange").value.trim();
    const symbol = $("symbol").value.trim().toUpperCase();
    const timeframe = $("timeframe").value;
    const data = await api(`/market/analyze/${encodeURIComponent(exchange)}/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(timeframe)}`);
    renderJson($("analysisResult"), data);
    await refreshMe();
  } catch (error) {
    $("analysisResult").textContent = error.message;
  }
});

$("reportForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    $("marketReportBox").className = "empty";
    $("marketReportBox").textContent = "در حال ساخت گزارش بازار...";
    const symbols = encodeURIComponent($("reportSymbols").value.trim());
    const timeframe = encodeURIComponent($("reportTimeframe").value);
    const report = await api(`/report/market?symbols=${symbols}&timeframe=${timeframe}&limit=100`);
    renderMarketReport(report);
    await refreshMe();
  } catch (error) {
    $("marketReportBox").className = "empty";
    $("marketReportBox").textContent = error.message;
  }
});

$("assignPlanBtn").addEventListener("click", async () => {
  try {
    const userId = $("targetUserId").value;
    const payload = {
      plan_code: $("targetPlan").value,
      days: Number($("targetDays").value || 30),
    };
    await api(`/admin/users/${userId}/subscription`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await loadAdmin();
    toast("اشتراک اختصاص داده شد.");
  } catch (error) {
    toast(error.message);
  }
});

$("logoutBtn").addEventListener("click", clearSession);
$("refreshMeBtn").addEventListener("click", () => refreshMe().catch((error) => toast(error.message)));
$("loadAdminBtn").addEventListener("click", () => loadAdmin().catch((error) => toast(error.message)));
$("loadManagedAdminBtn").addEventListener("click", () => loadManagedAdmin().catch((error) => toast(error.message)));
$("loadInvoicesAdminBtn").addEventListener("click", () => loadInvoicesAdmin().catch((error) => toast(error.message)));

renderSession();
if (state.token) refreshMe().catch(() => clearSession());
