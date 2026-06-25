(function () {
  const storageKey = "market_ai_active_tab";
  const tabOrder = [
    "account",
    "managed-portfolio",
    "chart",
    "report",
    "iran-market",
    "news",
    "assistant",
    "analysis",
    "trade-plan",
    "social",
    "performance",
    "feedback",
    "customize",
    "admin",
    "revenue",
  ];

  const labels = {
    fa: {
      account: "حساب",
      "managed-portfolio": "درآمد ثابت ایران",
      chart: "چارت زنده",
      report: "گزارش بازار",
      "iran-market": "بورس ایران",
      news: "اخبار",
      assistant: "دستیار",
      analysis: "تحلیل نماد",
      "trade-plan": "پلن معامله",
      social: "تحلیلگران",
      performance: "عملکرد مدل",
      feedback: "نظرات",
      customize: "چیدمان",
      admin: "ادمین",
      revenue: "تقسیم سود",
    },
    en: {
      account: "Account",
      "managed-portfolio": "Iran Income",
      chart: "Live Chart",
      report: "Market Report",
      "iran-market": "Iran Market",
      news: "News",
      assistant: "Assistant",
      analysis: "Symbol Analysis",
      "trade-plan": "Trade Plan",
      social: "Analysts",
      performance: "Model Performance",
      feedback: "Comments",
      customize: "Layout",
      admin: "Admin",
      revenue: "Revenue",
    },
  };

  function lang() {
    return typeof currentLanguage === "function" ? currentLanguage() : "fa";
  }

  function label(blockId) {
    return labels[lang()]?.[blockId] || labels.fa[blockId] || blockId;
  }

  function blocks() {
    return Array.from(document.querySelectorAll(".dashboardBlock[data-block-id]"));
  }

  function blockById(blockId) {
    return document.querySelector(`.dashboardBlock[data-block-id="${blockId}"]`);
  }

  function isAvailable(block) {
    return Boolean(block) && !block.classList.contains("hidden");
  }

  function orderedBlockIds() {
    const existing = blocks().map((block) => block.dataset.blockId);
    const known = tabOrder.filter((id) => existing.includes(id));
    const extra = existing.filter((id) => !known.includes(id));
    return [...known, ...extra];
  }

  function firstAvailableId() {
    return orderedBlockIds().find((id) => isAvailable(blockById(id))) || "account";
  }

  function activeId() {
    const saved = localStorage.getItem(storageKey);
    return isAvailable(blockById(saved)) ? saved : firstAvailableId();
  }

  function selectTab(blockId) {
    const target = isAvailable(blockById(blockId)) ? blockId : firstAvailableId();
    localStorage.setItem(storageKey, target);
    refreshTabs();
  }

  function renderButtons() {
    const nav = document.getElementById("dashboardTabs");
    if (!nav) return;
    nav.setAttribute("aria-label", lang() === "en" ? "Dashboard sections" : "بخش‌های داشبورد");
    nav.innerHTML = orderedBlockIds()
      .map((id) => `<button type="button" data-dashboard-tab="${id}">${label(id)}</button>`)
      .join("");
    nav.querySelectorAll("[data-dashboard-tab]").forEach((button) => {
      button.addEventListener("click", () => selectTab(button.dataset.dashboardTab));
    });
  }

  function refreshTabs() {
    const nav = document.getElementById("dashboardTabs");
    if (!nav) return;
    const selected = activeId();
    blocks().forEach((block) => {
      block.classList.toggle("tabHidden", block.dataset.blockId !== selected);
    });
    nav.querySelectorAll("[data-dashboard-tab]").forEach((button) => {
      const target = blockById(button.dataset.dashboardTab);
      const available = isAvailable(target);
      button.classList.toggle("hidden", !available);
      button.classList.toggle("active", button.dataset.dashboardTab === selected);
      button.setAttribute("aria-selected", button.dataset.dashboardTab === selected ? "true" : "false");
    });
  }

  function syncTabs() {
    renderButtons();
    refreshTabs();
  }

  window.selectDashboardTab = selectTab;
  window.refreshDashboardTabs = syncTabs;
  window.addEventListener("market-ai-language-change", syncTabs);

  window.addEventListener("DOMContentLoaded", () => {
    const content = document.getElementById("dashboardContent");
    syncTabs();
    if (content) {
      new MutationObserver(syncTabs).observe(content, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class", "data-block-id"],
      });
    }
  });
})();
