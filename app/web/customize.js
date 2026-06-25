const customizationState = {
  order: JSON.parse(localStorage.getItem("market_ai_block_order") || "[]"),
};

localStorage.removeItem("market_ai_theme");
document.body.classList.remove("compactMode");

function dashboardBlocks() {
  return Array.from(document.querySelectorAll(".dashboardBlock"));
}

function registerDynamicBlocks() {
  const known = [
    ["feedbackPanel", "feedback"],
    ["iranMarketPanel", "iran-market"],
    ["performancePanel", "performance"],
    ["newsPanel", "news"],
    ["socialPanel", "social"],
    ["revenuePanel", "revenue"],
  ];
  let changed = false;
  known.forEach(([elementId, blockId]) => {
    const element = document.getElementById(elementId);
    if (element && !element.classList.contains("dashboardBlock")) {
      element.classList.add("dashboardBlock");
      element.dataset.blockId = blockId;
      changed = true;
    }
  });
  if (changed) {
    applyBlockOrder();
    renderLayoutList();
  }
}

function applyBlockOrder() {
  const order = customizationState.order || [];
  if (!order.length) return;
  const container = document.getElementById("dashboardContent") || document.querySelector(".shell");
  const blocks = dashboardBlocks();
  const byId = new Map(blocks.map((block) => [block.dataset.blockId, block]));
  order.forEach((id) => {
    const block = byId.get(id);
    if (block) container.appendChild(block);
  });
}

function saveBlockOrder() {
  customizationState.order = dashboardBlocks().map((block) => block.dataset.blockId);
  localStorage.setItem("market_ai_block_order", JSON.stringify(customizationState.order));
}

function moveBlock(blockId, direction) {
  const block = document.querySelector(`[data-block-id="${blockId}"]`);
  if (!block) return;
  if (direction < 0 && block.previousElementSibling?.classList.contains("dashboardBlock")) {
    block.parentNode.insertBefore(block, block.previousElementSibling);
  }
  if (direction > 0 && block.nextElementSibling?.classList.contains("dashboardBlock")) {
    block.parentNode.insertBefore(block.nextElementSibling, block);
  }
  saveBlockOrder();
  renderLayoutList();
}

function resetLayout() {
  localStorage.removeItem("market_ai_block_order");
  window.location.reload();
}

function ensureCustomizePanel() {
  if (document.getElementById("customizePanel")) return;
  const container = document.getElementById("dashboardContent") || document.querySelector(".shell");
  if (!container) return;
  const panel = document.createElement("section");
  panel.id = "customizePanel";
  panel.className = "panel customizePanel dashboardBlock";
  panel.dataset.blockId = "customize";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2 data-customize-title>ترتیب داشبورد</h2>
        <p class="hint" data-customize-hint>بخش‌های داشبورد را برای خودت جابه‌جا کن.</p>
      </div>
      <button id="toggleCustomizeBtn" class="ghost" type="button">نمایش / مخفی</button>
    </div>
    <div id="customizeBody" class="customizeBody hidden">
      <div class="customizeTools">
        <button id="resetLayoutBtn" class="ghost" type="button">بازنشانی ترتیب</button>
      </div>
      <div id="layoutList" class="layoutList"></div>
    </div>
  `;
  container.appendChild(panel);
  document.getElementById("toggleCustomizeBtn").addEventListener("click", () => {
    document.getElementById("customizeBody").classList.toggle("hidden");
  });
  document.getElementById("resetLayoutBtn").addEventListener("click", resetLayout);
  renderLayoutList();
}

function blockTitle(block) {
  return block.querySelector(".panelHeader h2")?.textContent || block.dataset.blockId;
}

function renderLayoutList() {
  const list = document.getElementById("layoutList");
  if (!list) return;
  list.innerHTML = dashboardBlocks().map((block) => `
    <div class="layoutItem">
      <span>${blockTitle(block)}</span>
      <div>
        <button class="ghost" type="button" data-move-up="${block.dataset.blockId}">↑</button>
        <button class="ghost" type="button" data-move-down="${block.dataset.blockId}">↓</button>
      </div>
    </div>
  `).join("");
  list.querySelectorAll("[data-move-up]").forEach((button) => {
    button.addEventListener("click", () => moveBlock(button.dataset.moveUp, -1));
  });
  list.querySelectorAll("[data-move-down]").forEach((button) => {
    button.addEventListener("click", () => moveBlock(button.dataset.moveDown, 1));
  });
}

function applyCustomizeLanguage() {
  const lang = typeof currentLanguage === "function" ? currentLanguage() : "fa";
  const text = lang === "en"
    ? {
        title: "Dashboard Order",
        hint: "Move dashboard sections into the order you prefer.",
        toggle: "Show / Hide",
        resetLayout: "Reset Order",
      }
    : {
        title: "ترتیب داشبورد",
        hint: "بخش‌های داشبورد را برای خودت جابه‌جا کن.",
        toggle: "نمایش / مخفی",
        resetLayout: "بازنشانی ترتیب",
      };
  const panel = document.getElementById("customizePanel");
  if (!panel) return;
  panel.querySelector("[data-customize-title]").textContent = text.title;
  panel.querySelector("[data-customize-hint]").textContent = text.hint;
  document.getElementById("toggleCustomizeBtn").textContent = text.toggle;
  document.getElementById("resetLayoutBtn").textContent = text.resetLayout;
}

window.addEventListener("market-ai-language-change", applyCustomizeLanguage);

window.addEventListener("DOMContentLoaded", () => {
  applyBlockOrder();
  ensureCustomizePanel();
  applyCustomizeLanguage();
  registerDynamicBlocks();
  const shell = document.querySelector(".shell");
  const container = document.getElementById("dashboardContent") || shell;
  if (container) {
    new MutationObserver(registerDynamicBlocks).observe(container, { childList: true, subtree: false });
  }
});
