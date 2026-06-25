(function () {
  const assets = [
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "ADA",
    "DOGE",
    "LINK",
    "AVAX",
    "TON",
    "TRX",
    "DOT",
    "MATIC",
    "LTC",
    "BCH",
    "ATOM",
    "NEAR",
    "APT",
    "ARB",
    "OP",
    "UNI",
    "AAVE",
    "FIL",
    "ETC",
    "ICP",
    "INJ",
    "SUI",
    "PEPE",
    "SHIB",
  ];
  const quotes = ["USDT", "USDC", "BTC", "ETH"];
  const commodities = [
    {
      symbol: "XAUUSD",
      label: "XAUUSD - طلا",
      type: "commodity",
      description: "طلا / Gold - USD per troy ounce",
      aliases: ["GOLD", "XAU", "طلا"],
    },
    {
      symbol: "XAGUSD",
      label: "XAGUSD - نقره",
      type: "commodity",
      description: "نقره / Silver - USD per troy ounce",
      aliases: ["SILVER", "XAG", "نقره"],
    },
    {
      symbol: "WTIUSD",
      label: "WTIUSD - نفت خام WTI",
      type: "commodity",
      description: "نفت خام WTI / US Oil - USD per barrel",
      aliases: ["USOIL", "OIL", "WTI", "نفت"],
    },
    {
      symbol: "BRENTUSD",
      label: "BRENTUSD - نفت برنت",
      type: "commodity",
      description: "نفت برنت / Brent Oil - USD per barrel",
      aliases: ["UKOIL", "BRENT", "برنت"],
    },
    {
      symbol: "NGAS",
      label: "NGAS - گاز طبیعی",
      type: "commodity",
      description: "گاز طبیعی / Natural Gas",
      aliases: ["NATGAS", "GAS", "گاز"],
    },
    {
      symbol: "COPPER",
      label: "COPPER - مس",
      type: "commodity",
      description: "مس / Copper",
      aliases: ["HG", "COPPERUSD", "مس"],
    },
  ];
  const inputIds = ["chartSymbol", "symbol", "reportSymbols", "newsSymbols"];
  const multiValueInputs = new Set(["reportSymbols", "newsSymbols"]);
  const box = document.createElement("div");
  const boundInputs = new WeakSet();
  let activeInput = null;
  let activeIndex = -1;
  let currentItems = [];
  let debounceTimer = null;

  box.id = "symbolSuggestBox";
  box.className = "symbolSuggestBox hidden";
  document.body.appendChild(box);

  function clean(value) {
    return (value || "").trim().toUpperCase().replace(/\s+/g, "");
  }

  function addSuggestion(items, seen, symbol, type) {
    if (items.length >= 12 || seen.has(symbol)) return;
    seen.add(symbol);
    items.push({
      symbol,
      label: symbol,
      type,
      description:
        type === "pair"
          ? `جفت ارز ${symbol} برای مقایسه دو دارایی`
          : `نماد اسپات ${symbol}`,
    });
  }

  function addItem(items, seen, item) {
    if (items.length >= 12 || seen.has(item.symbol)) return;
    seen.add(item.symbol);
    items.push(item);
  }

  function localSuggestions(query) {
    const q = clean(query);
    const items = [];
    const seen = new Set();
    if (!q) return items;

    commodities.forEach((item) => {
      const haystack = [item.symbol, item.label, item.description, ...item.aliases].join(" ").toUpperCase();
      if (haystack.includes(q)) addItem(items, seen, item);
    });

    if (q.includes("/")) {
      const [baseQuery, quoteQuery = ""] = q.split("/");
      const bases = assets.filter((asset) => !baseQuery || asset.startsWith(baseQuery));
      const quoteMatches = assets.filter(
        (asset) => asset !== baseQuery && (!quoteQuery || asset.startsWith(quoteQuery))
      );
      if (baseQuery.length >= 2 && !bases.includes(baseQuery)) bases.unshift(baseQuery);
      bases.forEach((base) => {
        quoteMatches.forEach((quote) => {
          if (base !== quote) addSuggestion(items, seen, `${base}/${quote}`, "pair");
        });
      });
      return items;
    }

    assets.forEach((asset) => {
      quotes.forEach((quote) => {
        const symbol = `${asset}${quote}`;
        if (asset !== quote && !(asset === "BTC" && quote === "ETH") && symbol.startsWith(q)) {
          addSuggestion(items, seen, symbol, "spot");
        }
      });
    });
    assets
      .filter((asset) => asset.startsWith(q))
      .forEach((asset) => {
        addSuggestion(items, seen, `${asset}USDT`, "spot");
        if (asset !== "ETH") addSuggestion(items, seen, `${asset}/ETH`, "pair");
        if (asset !== "BTC") addSuggestion(items, seen, `${asset}/BTC`, "pair");
      });
    return items;
  }

  function getSearchToken(input) {
    if (!multiValueInputs.has(input.id)) return input.value;
    const parts = input.value.split(",");
    return parts[parts.length - 1] || "";
  }

  function setInputValue(input, symbol) {
    if (multiValueInputs.has(input.id)) {
      const parts = input.value.split(",");
      parts[parts.length - 1] = symbol;
      input.value = parts.map((part) => part.trim()).filter(Boolean).join(",");
    } else {
      input.value = symbol;
    }
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  async function fetchSuggestions(token) {
    const fallback = localSuggestions(token);
    if (!window.api || clean(token).length < 1) return fallback;
    try {
      const data = await window.api(`/symbols/search?q=${encodeURIComponent(token)}&limit=12`);
      return data.items && data.items.length ? data.items : fallback;
    } catch (error) {
      return fallback;
    }
  }

  function positionBox(input) {
    const rect = input.getBoundingClientRect();
    const width = Math.min(rect.width, window.innerWidth - 16);
    const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));
    box.style.width = `${width}px`;
    box.style.left = `${left + window.scrollX}px`;
    box.style.top = `${rect.bottom + window.scrollY + 6}px`;
  }

  function hideBox() {
    box.classList.add("hidden");
    box.innerHTML = "";
    activeIndex = -1;
    currentItems = [];
  }

  function render(items, input) {
    currentItems = items;
    activeIndex = -1;
    if (!items.length) {
      hideBox();
      return;
    }
    box.innerHTML = items
      .map(
        (item, index) => `
          <button class="symbolSuggestItem" data-index="${index}" type="button">
            <span>
              <b>${item.label || item.symbol}</b>
              <small>${item.description || ""}</small>
            </span>
            <em>${item.type === "pair" ? "PAIR" : item.type === "commodity" ? "CMDTY" : "SPOT"}</em>
          </button>
        `
      )
      .join("");
    positionBox(input);
    box.classList.remove("hidden");
  }

  function setActiveIndex(nextIndex) {
    const buttons = [...box.querySelectorAll(".symbolSuggestItem")];
    buttons.forEach((button) => button.classList.remove("active"));
    activeIndex = nextIndex;
    if (buttons[activeIndex]) buttons[activeIndex].classList.add("active");
  }

  function choose(index) {
    if (!activeInput || !currentItems[index]) return;
    setInputValue(activeInput, currentItems[index].symbol);
    hideBox();
  }

  function bindInput(input) {
    if (boundInputs.has(input)) return;
    boundInputs.add(input);
    input.setAttribute("autocomplete", "off");
    input.addEventListener("input", () => {
      activeInput = input;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async () => {
        const token = getSearchToken(input);
        const items = await fetchSuggestions(token);
        render(items, input);
      }, 120);
    });
    input.addEventListener("focus", () => {
      activeInput = input;
      const token = getSearchToken(input);
      if (clean(token)) render(localSuggestions(token), input);
    });
    input.addEventListener("keydown", (event) => {
      if (box.classList.contains("hidden")) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex(Math.min(activeIndex + 1, currentItems.length - 1));
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex(Math.max(activeIndex - 1, 0));
      }
      if (event.key === "Enter" && activeIndex >= 0) {
        event.preventDefault();
        choose(activeIndex);
      }
      if (event.key === "Escape") hideBox();
    });
  }

  box.addEventListener("mousedown", (event) => event.preventDefault());
  box.addEventListener("click", (event) => {
    const button = event.target.closest(".symbolSuggestItem");
    if (!button) return;
    choose(Number(button.dataset.index));
  });
  document.addEventListener("click", (event) => {
    if (event.target === activeInput || box.contains(event.target)) return;
    hideBox();
  });
  window.addEventListener("resize", () => {
    if (activeInput && !box.classList.contains("hidden")) positionBox(activeInput);
  });
  window.addEventListener("scroll", () => {
    if (activeInput && !box.classList.contains("hidden")) positionBox(activeInput);
  }, true);

  inputIds
    .map((id) => document.getElementById(id))
    .filter(Boolean)
    .forEach(bindInput);

  const scanInputs = () => {
    inputIds
      .map((id) => document.getElementById(id))
      .filter(Boolean)
      .forEach(bindInput);
  };
  const observer = new MutationObserver(scanInputs);
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener("load", scanInputs);
})();
