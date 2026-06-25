function setupCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * ratio));
  canvas.height = Math.max(1, Math.floor(rect.height * ratio));
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { ctx, width: rect.width, height: rect.height };
}

function drawGrid(ctx, width, height) {
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "rgba(125, 139, 161, 0.14)";
  ctx.lineWidth = 1;
  for (let i = 1; i < 5; i += 1) {
    const y = (height / 5) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  for (let i = 1; i < 8; i += 1) {
    const x = (width / 8) * i;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
}

function drawLine(ctx, points, values, xForIndex, yForValue, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  let started = false;
  values.forEach((value, index) => {
    if (value === null || Number.isNaN(value)) return;
    const x = xForIndex(index);
    const y = yForValue(value);
    if (!started) {
      ctx.moveTo(x, y);
      started = true;
    } else {
      ctx.lineTo(x, y);
    }
  });
  if (started) ctx.stroke();
}

function renderPriceChart(data) {
  const canvas = document.getElementById("priceCanvas");
  const { ctx, width, height } = setupCanvas(canvas);
  const candles = data.candles || [];
  if (!candles.length) return;

  drawGrid(ctx, width, height);
  const highs = candles.map((item) => item.high);
  const lows = candles.map((item) => item.low);
  const indicatorValues = [...(data.indicators.ema20 || []), ...(data.indicators.ema50 || [])].filter((value) => value !== null);
  const maxPrice = Math.max(...highs, ...indicatorValues);
  const minPrice = Math.min(...lows, ...indicatorValues);
  const pad = (maxPrice - minPrice) * 0.08 || 1;
  const top = maxPrice + pad;
  const bottom = minPrice - pad;
  const count = candles.length;
  const step = width / count;
  const bodyWidth = Math.max(3, Math.min(10, step * 0.62));
  const xForIndex = (index) => index * step + step / 2;
  const yForValue = (value) => height - ((value - bottom) / (top - bottom)) * height;

  candles.forEach((candle, index) => {
    const x = xForIndex(index);
    const openY = yForValue(candle.open);
    const closeY = yForValue(candle.close);
    const highY = yForValue(candle.high);
    const lowY = yForValue(candle.low);
    const up = candle.close >= candle.open;
    ctx.strokeStyle = up ? "#2ea043" : "#f85149";
    ctx.fillStyle = up ? "rgba(46, 160, 67, 0.9)" : "rgba(248, 81, 73, 0.9)";
    ctx.beginPath();
    ctx.moveTo(x, highY);
    ctx.lineTo(x, lowY);
    ctx.stroke();
    ctx.fillRect(x - bodyWidth / 2, Math.min(openY, closeY), bodyWidth, Math.max(2, Math.abs(closeY - openY)));
  });

  drawLine(ctx, candles, data.indicators.ema20 || [], xForIndex, yForValue, "#d29922");
  drawLine(ctx, candles, data.indicators.ema50 || [], xForIndex, yForValue, "#58a6ff");

  ctx.fillStyle = "#7d8ba1";
  ctx.font = "12px Arial";
  ctx.fillText(top.toFixed(2), 8, 16);
  ctx.fillText(bottom.toFixed(2), 8, height - 8);
}

function renderRsiChart(data) {
  const canvas = document.getElementById("rsiCanvas");
  const { ctx, width, height } = setupCanvas(canvas);
  const rsi = data.indicators.rsi14 || [];
  drawGrid(ctx, width, height);
  const xForIndex = (index) => index * (width / Math.max(1, rsi.length)) + width / Math.max(1, rsi.length) / 2;
  const yForValue = (value) => height - (value / 100) * height;

  ctx.strokeStyle = "rgba(248, 81, 73, 0.5)";
  ctx.beginPath();
  ctx.moveTo(0, yForValue(70));
  ctx.lineTo(width, yForValue(70));
  ctx.stroke();
  ctx.strokeStyle = "rgba(46, 160, 67, 0.5)";
  ctx.beginPath();
  ctx.moveTo(0, yForValue(30));
  ctx.lineTo(width, yForValue(30));
  ctx.stroke();

  drawLine(ctx, rsi, rsi, xForIndex, yForValue, "#a371f7");
  ctx.fillStyle = "#7d8ba1";
  ctx.font = "12px Arial";
  ctx.fillText("RSI 70", 8, yForValue(70) - 5);
  ctx.fillText("RSI 30", 8, yForValue(30) + 14);
}
