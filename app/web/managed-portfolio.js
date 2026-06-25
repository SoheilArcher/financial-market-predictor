function ensureManagedPortfolioPanel() {
  if (document.getElementById("managedPortfolioPanel")) {
    bindManagedPortfolioPanel();
    return;
  }
  const accountSection = document.querySelector('[data-block-id="account"]');
  if (!accountSection) return;
  const panel = document.createElement("section");
  panel.id = "managedPortfolioPanel";
  panel.className = "panel hidden dashboardBlock";
  panel.dataset.blockId = "managed-portfolio";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>درآمد ثابت بورس ایران</h2>
        <p class="hint">محاسبه و ثبت درخواست محصول مستقل بازار سرمایه ایران؛ جدا از کریپتو، بازار جهانی و ترید پرریسک.</p>
      </div>
      <button id="loadManagedRequestsBtn" class="ghost" type="button">درخواست‌های من</button>
    </div>
    <form id="managedPortfolioForm" class="managedPortfolioGrid">
      <label>سرمایه <input id="managedCapital" type="number" min="1" step="1" value="1000" /></label>
      <label>ارز سرمایه
        <select id="managedCurrency">
          <option>USDT</option>
          <option>USD</option>
          <option>IRR</option>
        </select>
      </label>
      <label>بازده هدف سالانه % <input id="iranYieldAnnual" type="number" step="0.1" value="35" /></label>
      <label>کارمزد شما % <input id="managedFee" type="number" min="0" max="50" step="0.1" value="5" /></label>
      <label>مالیات/هزینه % <input id="managedTax" type="number" min="0" max="50" step="0.1" value="0" /></label>
      <label>پرداخت / تسویه
        <select id="managedPayout">
          <option>USDT</option>
        </select>
      </label>
      <label>شبکه پرداخت
        <select id="managedNetwork">
          <option>TRC20</option>
          <option>ERC20</option>
          <option>BEP20</option>
        </select>
      </label>
      <label class="wide">توضیحات <input id="managedNotes" placeholder="مثلاً سرمایه‌گذاری یک‌ساله یا برداشت سود ماهانه" /></label>
      <button class="primary" type="submit">ثبت درخواست</button>
      <button id="iranYieldQuoteBtn" class="ghost" type="button">محاسبه پلن ایران</button>
    </form>
    <div id="managedPortfolioBox" class="empty">اول «محاسبه پلن ایران» را بزنید تا سود ناخالص، کارمزد و سود خالص نمایش داده شود.</div>
    <div class="cryptoWalletBox">
      <h3>آدرس تسویه USDT</h3>
      <form id="cryptoWalletForm" class="managedPortfolioGrid">
        <label>برچسب <input id="cryptoWalletLabel" value="Main wallet" /></label>
        <label>ارز
          <select id="cryptoWalletCurrency">
            <option>USDT</option>
          </select>
        </label>
        <label>شبکه
          <select id="cryptoWalletNetwork">
            <option>TRC20</option>
            <option>ERC20</option>
            <option>BEP20</option>
          </select>
        </label>
        <label class="wide">آدرس دریافت USDT <input id="cryptoWalletAddress" placeholder="آدرس دریافت سود/تسویه" /></label>
        <button class="ghost" type="submit">ثبت آدرس تسویه</button>
      </form>
      <div id="cryptoWalletList" class="empty">آدرس تسویه‌ای ثبت نشده است.</div>
    </div>
  `;
  accountSection.insertAdjacentElement("afterend", panel);
  bindManagedPortfolioPanel();
}

function bindManagedPortfolioPanel() {
  const panel = document.getElementById("managedPortfolioPanel");
  if (!panel || panel.dataset.bound === "true") return;
  panel.dataset.bound = "true";
  document.getElementById("managedPortfolioForm").addEventListener("submit", submitManagedPortfolio);
  document.getElementById("iranYieldQuoteBtn").addEventListener("click", loadIranYieldQuote);
  document.getElementById("loadManagedRequestsBtn").addEventListener("click", loadManagedRequests);
  document.getElementById("cryptoWalletForm").addEventListener("submit", submitCryptoWallet);
  loadCryptoWallets();
}

function renderIranYieldQuote(quote) {
  document.getElementById("managedPortfolioBox").className = "reportBox";
  document.getElementById("managedPortfolioBox").innerHTML = `
    <div class="managedNotice">${quote.summary_fa}</div>
    <div class="cryptoInvoice">
      <div><span>سرمایه</span><b>${quote.capital_amount}</b></div>
      <div><span>بازده هدف سالانه</span><b>${quote.annual_return_percent}%</b></div>
      <div><span>سود ناخالص سالانه</span><b>${quote.gross_yearly_profit}</b></div>
      <div><span>سود ناخالص ماهانه</span><b>${quote.gross_monthly_profit}</b></div>
      <div><span>کارمزد پلتفرم</span><b>${quote.platform_fee_amount}</b></div>
      <div><span>هزینه/مالیات</span><b>${quote.tax_amount}</b></div>
      <div><span>سود خالص سالانه</span><b>${quote.net_yearly_profit}</b></div>
      <div><span>بازده خالص</span><b>${quote.net_return_percent}%</b></div>
    </div>
  `;
}

async function loadIranYieldQuote() {
  const box = document.getElementById("managedPortfolioBox");
  try {
    box.className = "empty";
    box.textContent = "در حال محاسبه پلن درآمد ثابت ایران...";
    const quote = await api("/iran-yield/quote", {
      method: "POST",
      body: JSON.stringify({
        capital_amount: Number(document.getElementById("managedCapital").value || 0),
        annual_return_percent: Number(document.getElementById("iranYieldAnnual").value || 35),
        platform_fee_percent: Number(document.getElementById("managedFee").value || 5),
        tax_percent: Number(document.getElementById("managedTax").value || 0),
      }),
    });
    renderIranYieldQuote(quote);
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

function managedPayload() {
  const payload = {
    capital_amount: Number(document.getElementById("managedCapital").value || 0),
    capital_currency: document.getElementById("managedCurrency").value,
    preferred_market: "iran_fixed_income",
    risk_level: "low",
    gross_profit_percent: Number(document.getElementById("iranYieldAnnual").value || 35),
    fee_percent: Number(document.getElementById("managedFee").value || 0),
    tax_percent: Number(document.getElementById("managedTax").value || 0),
    payout_currency: document.getElementById("managedPayout").value,
    notes: document.getElementById("managedNotes").value.trim(),
    country: state.user?.country || "",
  };
  return payload;
}

function renderManagedRequests(items) {
  const rows = (items || []).map((item) => {
    const report = item.latest_report || {};
    return `
      <tr>
        <td>${item.id}</td>
        <td>${item.capital_amount} ${item.capital_currency}</td>
        <td>${item.preferred_market}</td>
        <td>${item.risk_level}</td>
        <td>${item.status}</td>
        <td>${report.gross_profit_percent ?? 0}%</td>
        <td>${report.fee_amount ?? 0}</td>
        <td>${report.tax_amount ?? 0}</td>
        <td>${report.net_profit ?? 0}</td>
      </tr>
    `;
  }).join("");
  document.getElementById("managedPortfolioBox").className = "reportBox";
  document.getElementById("managedPortfolioBox").innerHTML = `
    <div class="managedNotice">این محصول مخصوص درآمد ثابت بورس ایران است و با بازار کریپتو یا بازار جهانی ترکیب نشده است. درخواست‌ها برای بررسی و قرارداد ثبت می‌شوند.</div>
    <div class="tableWrap">
      <table>
        <thead><tr><th>ID</th><th>سرمایه</th><th>بازار</th><th>ریسک</th><th>وضعیت</th><th>بازده</th><th>کارمزد</th><th>هزینه</th><th>سود خالص</th></tr></thead>
        <tbody>${rows || "<tr><td colspan='9'>درخواستی ثبت نشده است.</td></tr>"}</tbody>
      </table>
    </div>
  `;
}

function renderCryptoInvoice(invoice) {
  document.getElementById("managedPortfolioBox").className = "reportBox";
  document.getElementById("managedPortfolioBox").innerHTML = `
    <div class="managedNotice">برای ورود به پلن درآمد ثابت ایران، فقط با ${invoice.currency} روی شبکه ${invoice.network} پرداخت کنید. پرداخت روی شبکه اشتباه ممکن است قابل بازیابی نباشد.</div>
    <div class="cryptoInvoice">
      <div><span>مبلغ</span><b>${invoice.amount} ${invoice.currency}</b></div>
      <div><span>شبکه</span><b>${invoice.network}</b></div>
      <div class="wide"><span>آدرس پرداخت</span><code>${invoice.deposit_address}</code></div>
      <div><span>Memo</span><b>${invoice.memo || "-"}</b></div>
      <div><span>وضعیت</span><b>${invoice.status}</b></div>
    </div>
    <form id="cryptoProofForm" class="managedPortfolioGrid">
      <label class="wide">Tx Hash <input id="cryptoTxHash" required placeholder="هش تراکنش را بعد از پرداخت وارد کنید" /></label>
      <label class="wide">کیف پول فرستنده <input id="cryptoPayerWallet" placeholder="اختیاری" /></label>
      <button class="primary" type="submit">ثبت رسید پرداخت</button>
    </form>
  `;
  document.getElementById("cryptoProofForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const updated = await api(`/crypto-payments/invoices/${invoice.id}/proof`, {
      method: "POST",
      body: JSON.stringify({
        tx_hash: document.getElementById("cryptoTxHash").value.trim(),
        payer_wallet: document.getElementById("cryptoPayerWallet").value.trim(),
      }),
    });
    renderCryptoInvoice(updated);
  });
}

async function submitManagedPortfolio(event) {
  event.preventDefault();
  const box = document.getElementById("managedPortfolioBox");
  try {
    box.className = "empty";
    box.textContent = "در حال ثبت درخواست...";
    const item = await api("/managed-portfolios/requests", {
      method: "POST",
      body: JSON.stringify(managedPayload()),
    });
    const invoice = await api("/crypto-payments/invoices", {
      method: "POST",
      body: JSON.stringify({
        amount: item.capital_amount,
        currency: item.payout_currency,
        network: document.getElementById("managedNetwork").value,
        purpose: "managed_portfolio",
        managed_request_id: item.id,
      }),
    });
    renderCryptoInvoice(invoice);
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

async function loadManagedRequests() {
  const box = document.getElementById("managedPortfolioBox");
  try {
    box.className = "empty";
    box.textContent = "در حال دریافت درخواست‌ها...";
    const data = await api("/managed-portfolios/requests");
    renderManagedRequests(data.items || []);
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

function renderCryptoWallets(items) {
  const rows = (items || []).map((item) => `
    <tr>
      <td>${item.label}</td>
      <td>${item.currency}</td>
      <td>${item.network}</td>
      <td><code>${item.wallet_address}</code></td>
      <td>تسویه</td>
      <td>${item.status}</td>
    </tr>
  `).join("");
  document.getElementById("cryptoWalletList").className = "tableWrap";
  document.getElementById("cryptoWalletList").innerHTML = `
    <table>
      <thead><tr><th>عنوان</th><th>ارز</th><th>شبکه</th><th>آدرس</th><th>کاربرد</th><th>وضعیت</th></tr></thead>
      <tbody>${rows || "<tr><td colspan='6'>آدرس تسویه‌ای ثبت نشده است.</td></tr>"}</tbody>
    </table>
  `;
}

async function loadCryptoWallets() {
  if (!state.token) return;
  try {
    const data = await api("/crypto-wallets");
    renderCryptoWallets(data.items || []);
  } catch {
    document.getElementById("cryptoWalletList").className = "empty";
    document.getElementById("cryptoWalletList").textContent = "کیف پول‌ها فعلاً قابل دریافت نیستند.";
  }
}

async function submitCryptoWallet(event) {
  event.preventDefault();
  const box = document.getElementById("cryptoWalletList");
  try {
    box.className = "empty";
    box.textContent = "در حال ثبت کیف پول...";
    await api("/crypto-wallets", {
      method: "POST",
      body: JSON.stringify({
        label: document.getElementById("cryptoWalletLabel").value.trim(),
        currency: document.getElementById("cryptoWalletCurrency").value,
        network: document.getElementById("cryptoWalletNetwork").value,
        wallet_address: document.getElementById("cryptoWalletAddress").value.trim(),
        wallet_type: "self_custody",
      }),
    });
    document.getElementById("cryptoWalletAddress").value = "";
    await loadCryptoWallets();
  } catch (error) {
    box.className = "empty";
    box.textContent = error.message;
  }
}

function renderManagedAccess() {
  ensureManagedPortfolioPanel();
  const panel = document.getElementById("managedPortfolioPanel");
  if (!panel) return;
  panel.classList.toggle("hidden", !state.token || !state.user);
  if (state.token && state.user) loadCryptoWallets();
}

const originalRenderSessionForManaged = renderSession;
renderSession = function patchedManagedRenderSession() {
  originalRenderSessionForManaged();
  renderManagedAccess();
};

ensureManagedPortfolioPanel();
renderManagedAccess();
