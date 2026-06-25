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
  renderSession();
}

function renderSession() {
  const isLoggedIn = Boolean(state.token && state.user);
  $("logoutBtn").classList.toggle("hidden", !isLoggedIn);
  $("authForm").classList.toggle("hidden", isLoggedIn);
  $("accountPanel").classList.toggle("hidden", !isLoggedIn);
  $("adminPanel").classList.toggle("hidden", !isLoggedIn || state.user?.role !== "admin");
  $("sessionText").textContent = isLoggedIn
    ? "وارد حساب شدید. حالا می‌توانید اشتراک و تحلیل‌ها را مدیریت کنید."
    : "برای تست محصول وارد حساب شوید یا ثبت‌نام کنید.";

  if (isLoggedIn) {
    $("accountEmail").textContent = state.user.email;
    $("accountStatus").textContent = state.user.status;
    $("roleBadge").textContent = state.user.role;
    $("roleBadge").className = `badge ${state.user.role}`;
    $("email").value = "";
    $("password").value = "";
    $("fullName").value = "";
  } else {
    $("meBox").textContent = "هنوز وارد نشده‌اید.";
    $("accountEmail").textContent = "-";
    $("accountStatus").textContent = "-";
    $("roleBadge").textContent = "";
    $("roleBadge").className = "badge";
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

async function loadAdmin() {
  const users = await api("/admin/users");
  renderUsers(users);
}

document.querySelectorAll("[data-auth-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    state.authMode = button.dataset.authMode;
    document.querySelectorAll("[data-auth-mode]").forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    $("nameField").classList.toggle("hidden", state.authMode !== "register");
  });
});

$("authForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = {
      email: $("email").value.trim(),
      password: $("password").value,
    };
    if (state.authMode === "register") payload.full_name = $("fullName").value.trim() || null;
    const data = await api(`/auth/${state.authMode}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setSession(data.access_token, data.user);
    await refreshMe();
    toast("ورود موفق بود.");
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
    const data = await api(`/market/analyze/${exchange}/${symbol}?timeframe=${encodeURIComponent(timeframe)}`);
    renderJson($("analysisResult"), data);
    await refreshMe();
  } catch (error) {
    $("analysisResult").textContent = error.message;
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

renderSession();
if (state.token) refreshMe().catch(() => clearSession());
