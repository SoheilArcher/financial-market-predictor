function ensureManagedPortfolioPanel() {
  if (document.getElementById("managedPortfolioPanel")) return;
  const assistantPanel = document.getElementById("assistantForm")?.closest(".panel");
  if (!assistantPanel) return;
  const panel = document.createElement("section");
  panel.id = "managedPortfolioPanel";
  panel.className = "panel hidden dashboardBlock";
  panel.dataset.blockId = "managed-portfolio";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2>درخواست مدیریت / کپی‌پرتفو</h2>
        <p class="hint">ثبت درخواست، محاسبه کارمزد/هزینه و گزارش خالص؛ بدون دریافت وجه یا اجرای معامله داخل سیستم.</p>
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
      <label>بازار
        <select id="managedMarket">
          <option value="crypto">کریپتو</option>
          <option value="global">بازار جهانی</option>
          <option value="iran">بورس ایران</option>
          <option value="mixed">ترکیبی</option>
        </select>
      </label>
      <label>ریسک
        <select id="managedRisk">
          <option value="low">کم</option>
          <option value="medium" selected>متوسط</option>
          <option value="high">زیاد</option>
        </select>
      </label>
      <label>درصد سود/زیان گزارش <input id="managedGrossProfit" type="number" step="0.1" value="0" /></label>
      <label>کارمزد شما % <input id="managedFee" type="number" min="0" max="50" step="0.1" value="5" /></label>
      <label>مالیات/هزینه % <input id="managedTax" type="number" min="0" max="50" step="0.1" value="0" /></label>
      <label>تسویه
        <select id="managedPayout">
          <option>USDT</option>
          <option>BTC</option>
          <option>ETH</option>
        </select>
      </label>
      <label>شبکه پرداخت
        <select id="managedNetwork">
          <option>TRC20</option>
          <option>ERC20</option>
          <option>BEP20</option>
        </select>
      </label>
      <label class="wide">توضیحات <input id="managedNotes" placeholder="مثلاً فقط معاملات کم‌ریسک یا فقط بیت‌کوین" /></label>
      <button class="primary" type="submit">ثبت درخواست</button>
    </form>
    <div id="managedPortfolioBox" class="empty">بعد از ثبت درخواست، گزارش خالص و وضعیت بررسی اینجا نمایش داده می‌شود.</div>
  `;
  assistantPanel.insertAdjacentElement("afterend", panel);
  document.getElementById("managedPortfolioForm").addEventListener("submit", submitManagedPortfolio);
  document.getElementById("loadManagedRequestsBtn").addEventListener("click", loadManagedRequests);
}

function managedPayload() {
  return {
    capital_amount: Number(document.getElementById("managedCapital").value || 0),
    capital_currency: document.getElementById("managedCurrency").value,
    preferred_market: document.getElementById("managedMarket").value,
    risk_level: document.getElementById("managedRisk").value,
    gross_profit_percent: Number(document.getElementById("managedGrossProfit").value || 0),
    fee_percent: Number(document.getElementById("managedFee").value || 0),
    tax_percent: Number(document.getElementById("managedTax").value || 0),
    payout_currency: document.getElementById("managedPayout").value,
    notes: document.getElementById("managedNotes").value.trim(),
    country: state.user?.country || "",
  };
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
    <div class="managedNotice">این بخش فعلاً اجرای واقعی معامله، دریافت وجه یا پرداخت رمزارز انجام نمی‌دهد؛ درخواست‌ها برای بررسی و قرارداد ثبت می‌شوند.</div>
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
    <div class="managedNotice">فقط با ${invoice.currency} روی شبکه ${invoice.network} پرداخت کنید. پرداخت روی شبکه اشتباه ممکن است قابل بازیابی نباشد.</div>
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

function renderManagedAccess() {
  ensureManagedPortfolioPanel();
  const panel = document.getElementById("managedPortfolioPanel");
  if (!panel) return;
  panel.classList.toggle("hidden", !state.token || !state.user);
}

const originalRenderSessionForManaged = renderSession;
renderSession = function patchedManagedRenderSession() {
  originalRenderSessionForManaged();
  renderManagedAccess();
};

ensureManagedPortfolioPanel();
renderManagedAccess();
