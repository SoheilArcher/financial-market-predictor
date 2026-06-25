const customizationState = {
  theme: JSON.parse(localStorage.getItem("market_ai_theme") || "{}"),
  order: JSON.parse(localStorage.getItem("market_ai_block_order") || "[]"),
};

const themePresets = {
  blue: {
    brand: "#2f81f7",
    bg: "#0b0f16",
    surface: "#111722",
    surface2: "#151d2a",
    surface3: "#1b2534",
    text: "#d7e0ea",
    textStrong: "#f3f7fb",
    muted: "#9aa8bc",
    line: "#263244",
    lineSoft: "#1c2736",
    inputBg: "#0d121b",
    chartBg: "#0a0f17",
  },
  green: {
    brand: "#2ea043",
    bg: "#07120d",
    surface: "#0e1b15",
    surface2: "#14261e",
    surface3: "#193126",
    text: "#d8eadf",
    textStrong: "#f4fff7",
    muted: "#9bb7a6",
    line: "#294536",
    lineSoft: "#20382b",
    inputBg: "#09150f",
    chartBg: "#06100b",
  },
  red: {
    brand: "#f85149",
    bg: "#140909",
    surface: "#201111",
    surface2: "#2b1717",
    surface3: "#361d1d",
    text: "#f1dddd",
    textStrong: "#fff3f3",
    muted: "#caa1a1",
    line: "#543030",
    lineSoft: "#422525",
    inputBg: "#170c0c",
    chartBg: "#120808",
  },
  gold: {
    brand: "#d29922",
    bg: "#11100a",
    surface: "#1b1810",
    surface2: "#252115",
    surface3: "#302a19",
    text: "#eee4c8",
    textStrong: "#fff8dc",
    muted: "#c2b27f",
    line: "#4c4225",
    lineSoft: "#3a321d",
    inputBg: "#151309",
    chartBg: "#0e0d07",
  },
  light: {
    brand: "#2563eb",
    bg: "#f4f7fb",
    surface: "#ffffff",
    surface2: "#eef3f8",
    surface3: "#e2e8f0",
    text: "#1f2937",
    textStrong: "#0f172a",
    muted: "#64748b",
    line: "#cbd5e1",
    lineSoft: "#dbe4ee",
    inputBg: "#ffffff",
    chartBg: "#f8fafc",
  },
};

function hexToRgb(hex) {
  const value = String(hex || "").replace("#", "");
  if (value.length !== 6) return null;
  return {
    r: parseInt(value.slice(0, 2), 16),
    g: parseInt(value.slice(2, 4), 16),
    b: parseInt(value.slice(4, 6), 16),
  };
}

function luminance(hex) {
  const rgb = hexToRgb(hex);
  if (!rgb) return 0;
  const channel = (value) => {
    const next = value / 255;
    return next <= 0.03928 ? next / 12.92 : ((next + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(rgb.r) + 0.7152 * channel(rgb.g) + 0.0722 * channel(rgb.b);
}

function readableOn(hex) {
  return luminance(hex) > 0.45 ? "#0f172a" : "#ffffff";
}

function applyTheme(theme = customizationState.theme) {
  const root = document.documentElement;
  const selected = themePresets[theme.preset] || {};
  const merged = { ...selected, ...theme };
  if (merged.brand) root.style.setProperty("--brand", merged.brand);
  if (merged.brand) root.style.setProperty("--brand-dark", merged.brand);
  if (merged.brand) root.style.setProperty("--brand-contrast", readableOn(merged.brand));
  if (merged.bg) root.style.setProperty("--bg", merged.bg);
  if (merged.surface) root.style.setProperty("--surface", merged.surface);
  if (merged.surface2) root.style.setProperty("--surface-2", merged.surface2);
  if (merged.surface3) root.style.setProperty("--surface-3", merged.surface3);
  if (merged.text) root.style.setProperty("--text", merged.text);
  if (merged.textStrong) root.style.setProperty("--text-strong", merged.textStrong);
  if (merged.muted) root.style.setProperty("--muted", merged.muted);
  if (merged.line) root.style.setProperty("--line", merged.line);
  if (merged.lineSoft) root.style.setProperty("--line-soft", merged.lineSoft);
  if (merged.inputBg) root.style.setProperty("--input-bg", merged.inputBg);
  if (merged.chartBg) root.style.setProperty("--chart-bg", merged.chartBg);
  document.body.classList.toggle("compactMode", Boolean(merged.compact));
}

function saveTheme(next) {
  customizationState.theme = { ...customizationState.theme, ...next };
  localStorage.setItem("market_ai_theme", JSON.stringify(customizationState.theme));
  applyTheme();
}

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
  const shell = document.querySelector(".shell");
  const blocks = dashboardBlocks();
  const byId = new Map(blocks.map((block) => [block.dataset.blockId, block]));
  order.forEach((id) => {
    const block = byId.get(id);
    if (block) shell.appendChild(block);
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
  const shell = document.querySelector(".shell");
  const topbar = document.querySelector(".topbar");
  if (!shell || !topbar) return;
  const panel = document.createElement("section");
  panel.id = "customizePanel";
  panel.className = "panel customizePanel";
  panel.innerHTML = `
    <div class="panelHeader">
      <div>
        <h2 data-customize-title>شخصی‌سازی ظاهر</h2>
        <p class="hint" data-customize-hint>رنگ و ترتیب بخش‌های داشبورد را برای خودت تنظیم کن.</p>
      </div>
      <button id="toggleCustomizeBtn" class="ghost" type="button">نمایش / مخفی</button>
    </div>
    <div id="customizeBody" class="customizeBody hidden">
      <div class="themeSwatches">
        <button type="button" data-theme-preset="blue" style="--swatch:#2f81f7" title="Blue"></button>
        <button type="button" data-theme-preset="green" style="--swatch:#2ea043" title="Green"></button>
        <button type="button" data-theme-preset="red" style="--swatch:#f85149" title="Red"></button>
        <button type="button" data-theme-preset="gold" style="--swatch:#d29922" title="Gold"></button>
        <button type="button" data-theme-preset="light" style="--swatch:#f4f7fb" title="Light"></button>
      </div>
      <div class="customizeTools">
        <label>
          رنگ اصلی
          <input id="brandColorInput" type="color" value="${customizationState.theme.brand || "#2f81f7"}" />
        </label>
        <label class="customizeCheck">
          <input id="compactModeInput" type="checkbox" ${customizationState.theme.compact ? "checked" : ""} />
          حالت فشرده
        </label>
        <button id="resetThemeBtn" class="ghost" type="button">بازنشانی رنگ</button>
        <button id="resetLayoutBtn" class="ghost" type="button">بازنشانی ترتیب</button>
      </div>
      <div id="layoutList" class="layoutList"></div>
    </div>
  `;
  shell.insertBefore(panel, topbar.nextElementSibling);
  document.getElementById("toggleCustomizeBtn").addEventListener("click", () => {
    document.getElementById("customizeBody").classList.toggle("hidden");
  });
  document.querySelectorAll("[data-theme-preset]").forEach((button) => {
    button.addEventListener("click", () => saveTheme({ preset: button.dataset.themePreset }));
  });
  document.getElementById("brandColorInput").addEventListener("input", (event) => saveTheme({ brand: event.target.value }));
  document.getElementById("compactModeInput").addEventListener("change", (event) => saveTheme({ compact: event.target.checked }));
  document.getElementById("resetThemeBtn").addEventListener("click", () => {
    localStorage.removeItem("market_ai_theme");
    customizationState.theme = {};
    window.location.reload();
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
        title: "Customize Appearance",
        hint: "Adjust dashboard colors and section order for yourself.",
        toggle: "Show / Hide",
        brand: "Primary Color",
        compact: "Compact Mode",
        resetTheme: "Reset Colors",
        resetLayout: "Reset Layout",
      }
    : {
        title: "شخصی‌سازی ظاهر",
        hint: "رنگ و ترتیب بخش‌های داشبورد را برای خودت تنظیم کن.",
        toggle: "نمایش / مخفی",
        brand: "رنگ اصلی",
        compact: "حالت فشرده",
        resetTheme: "بازنشانی رنگ",
        resetLayout: "بازنشانی ترتیب",
      };
  const panel = document.getElementById("customizePanel");
  if (!panel) return;
  panel.querySelector("[data-customize-title]").textContent = text.title;
  panel.querySelector("[data-customize-hint]").textContent = text.hint;
  document.getElementById("toggleCustomizeBtn").textContent = text.toggle;
  const brandLabel = panel.querySelector('label:has(#brandColorInput)');
  if (brandLabel?.firstChild) brandLabel.firstChild.textContent = `${text.brand}\n`;
  const compactLabel = panel.querySelector(".customizeCheck");
  if (compactLabel?.lastChild) compactLabel.lastChild.textContent = text.compact;
  document.getElementById("resetThemeBtn").textContent = text.resetTheme;
  document.getElementById("resetLayoutBtn").textContent = text.resetLayout;
}

window.addEventListener("market-ai-language-change", applyCustomizeLanguage);

applyTheme();
window.addEventListener("DOMContentLoaded", () => {
  applyBlockOrder();
  ensureCustomizePanel();
  applyCustomizeLanguage();
  registerDynamicBlocks();
  const shell = document.querySelector(".shell");
  if (shell) {
    new MutationObserver(registerDynamicBlocks).observe(shell, { childList: true, subtree: false });
  }
});
