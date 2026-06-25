const adminState = {
  token: localStorage.getItem("market_ai_token") || "",
  user: JSON.parse(localStorage.getItem("market_ai_user") || "null"),
};

const box = document.getElementById("adminPageBox");
const toastBox = document.getElementById("toast");

function toast(message) {
  toastBox.textContent = message;
  toastBox.classList.remove("hidden");
  window.setTimeout(() => toastBox.classList.add("hidden"), 3000);
}

async function adminApi(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${adminState.token}`,
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) throw new Error(data?.detail || `HTTP ${response.status}`);
  return data;
}

function ensureAdmin() {
  if (!adminState.token || adminState.user?.role !== "admin") {
    box.innerHTML = '<div class="empty">ابتدا در داشبورد با حساب ادمین وارد شوید.</div>';
    return false;
  }
  document.getElementById("adminSessionText").textContent = `ادمین: ${adminState.user.email}`;
  return true;
}

function renderUsers(items) {
  const rows = (items || []).map((item) => `
    <tr>
      <td>${item.id}</td><td>${item.email}</td><td>${item.country || "-"}</td>
      <td>${item.role}</td><td>${item.status}</td><td>${item.email_verified ? "yes" : "no"}</td>
      <td>${item.subscription?.plan?.code || "-"}</td>
    </tr>
  `).join("");
  box.innerHTML = `
    <h3>ثبت‌نام‌ها</h3>
    <table><thead><tr><th>ID</th><th>Email</th><th>Country</th><th>Role</th><th>Status</th><th>Email</th><th>Plan</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='7'>کاربری نیست.</td></tr>"}</tbody></table>
  `;
}

function renderRequests(data) {
  const rows = (data.items || []).map((item) => `
    <tr>
      <td>${item.id}</td><td>${item.user_id}</td><td>${item.capital_amount} ${item.capital_currency}</td>
      <td>${item.status}</td><td>${item.latest_report?.net_yearly_profit ?? "-"}</td><td>${item.latest_report?.net_return_percent ?? "-"}%</td>
      <td>${item.notes || "-"}</td>
      <td>
        <button data-request-status="approved" data-id="${item.id}" class="ghost">Approve</button>
        <button data-request-status="active" data-id="${item.id}" class="ghost">Active</button>
        <button data-request-status="rejected" data-id="${item.id}" class="ghost">Reject</button>
        <button data-request-status="settled" data-id="${item.id}" class="ghost">Settle</button>
      </td>
    </tr>
  `).join("");
  box.innerHTML = `
    <h3>درخواست‌های درآمد ثابت ایران</h3>
    <table><thead><tr><th>ID</th><th>User</th><th>Capital</th><th>Status</th><th>Net Profit</th><th>Return</th><th>Notes</th><th>Action</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='8'>درخواستی نیست.</td></tr>"}</tbody></table>
  `;
}

function renderInvoices(data) {
  const rows = (data.items || []).map((item) => `
    <tr>
      <td>${item.id}</td><td>${item.user_id}</td><td>${item.managed_request_id || "-"}</td>
      <td>${item.amount} ${item.currency}</td><td>${item.network}</td><td>${item.status}</td>
      <td><code>${item.tx_hash || "-"}</code></td>
      <td>
        <button data-invoice-status="confirmed" data-id="${item.id}" class="ghost">Confirm</button>
        <button data-invoice-status="rejected" data-id="${item.id}" class="ghost">Reject</button>
        <button data-invoice-status="refunded" data-id="${item.id}" class="ghost">Refund</button>
      </td>
    </tr>
  `).join("");
  box.innerHTML = `
    <h3>پرداخت‌ها</h3>
    <table><thead><tr><th>ID</th><th>User</th><th>Req</th><th>Amount</th><th>Network</th><th>Status</th><th>Tx</th><th>Action</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='8'>پرداختی نیست.</td></tr>"}</tbody></table>
  `;
}

function renderComments(data) {
  const rows = (data.items || []).map((item) => `
    <tr>
      <td>${item.id}</td><td>${item.user_email || item.user_id}</td><td>${item.target_type}</td>
      <td>${item.target_id}</td><td>${item.content}</td><td>${item.status}</td>
      <td>
        <button data-comment-status="visible" data-id="${item.id}" class="ghost">Visible</button>
        <button data-comment-status="review" data-id="${item.id}" class="ghost">Review</button>
        <button data-comment-status="hidden" data-id="${item.id}" class="ghost">Hide</button>
      </td>
    </tr>
  `).join("");
  box.innerHTML = `
    <h3>پیام‌ها و نظرات</h3>
    <table><thead><tr><th>ID</th><th>User</th><th>Type</th><th>Target</th><th>Content</th><th>Status</th><th>Action</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='7'>پیامی نیست.</td></tr>"}</tbody></table>
  `;
}

async function loadUsers() {
  if (!ensureAdmin()) return;
  renderUsers(await adminApi("/admin/users"));
}

async function loadRequests() {
  if (!ensureAdmin()) return;
  const status = document.getElementById("adminPageRequestStatus").value;
  renderRequests(await adminApi(`/admin/managed-requests${status ? `?status_filter=${status}` : ""}`));
}

async function loadInvoices() {
  if (!ensureAdmin()) return;
  const status = document.getElementById("adminPageInvoiceStatus").value;
  renderInvoices(await adminApi(`/admin/crypto-invoices${status ? `?status_filter=${status}` : ""}`));
}

async function loadComments() {
  if (!ensureAdmin()) return;
  const status = document.getElementById("adminPageCommentStatus").value;
  renderComments(await adminApi(`/admin/comments${status ? `?status_filter=${status}` : ""}`));
}

box.addEventListener("click", async (event) => {
  const requestButton = event.target.closest("[data-request-status]");
  const invoiceButton = event.target.closest("[data-invoice-status]");
  const commentButton = event.target.closest("[data-comment-status]");
  try {
    if (requestButton) {
      await adminApi(`/admin/managed-requests/${requestButton.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: requestButton.dataset.requestStatus }),
      });
      await loadRequests();
    }
    if (invoiceButton) {
      await adminApi(`/admin/crypto-invoices/${invoiceButton.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: invoiceButton.dataset.invoiceStatus }),
      });
      await loadInvoices();
    }
    if (commentButton) {
      await adminApi(`/admin/comments/${commentButton.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: commentButton.dataset.commentStatus }),
      });
      await loadComments();
    }
    toast("بروزرسانی شد.");
  } catch (error) {
    toast(error.message);
  }
});

document.getElementById("adminLoadUsers").addEventListener("click", loadUsers);
document.getElementById("adminLoadRequests").addEventListener("click", loadRequests);
document.getElementById("adminLoadInvoices").addEventListener("click", loadInvoices);
document.getElementById("adminLoadComments").addEventListener("click", loadComments);

ensureAdmin();
loadRequests().catch((error) => toast(error.message));
