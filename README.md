# NexTrade / financial-market-predictor

## AI Performance Engine

The platform stores every non-WAIT market analysis, market report item, and trade plan as a historical prediction in `performance_predictions`.

Tracked fields include:

- source type: `analysis`, `report`, `radar`, `trade_plan`, `news_signal`
- symbol, market type, timeframe, direction, confidence
- entry price, stop loss, take profit
- lifecycle: `PENDING`, `WIN`, `LOSS`, `EXPIRED`, `NO_DATA`
- max/min price after the signal, exit price, PnL percent, Persian reason, raw payload

WAIT signals are not saved or counted as wins/losses.

### Create Tables

```bash
python -m app.create_tables
```

### API

Generate signals normally:

```bash
GET /market/analyze/{exchange_name}/{symbol}?timeframe=5m
GET /report/market?symbols=BTCUSDT,ETHUSDT&timeframe=5m
GET /trade/plan/{symbol}?timeframe=5m
```

Evaluate and inspect model performance:

```bash
POST /performance/evaluate-pending
GET /performance/summary
GET /performance/history
GET /performance/by-symbol/{symbol}
GET /performance/by-timeframe/{timeframe}
```

`/performance/summary` returns total signals, evaluated signals, win/loss/expired/no-data counts, real win rate, average PnL, best/worst symbol, win rate by symbol/timeframe/confidence bucket, and the last 90 signals.

### Important Behavior

The evaluator fetches candles after `created_at` until `expires_at`.

- LONG wins when take profit is hit before stop loss.
- LONG loses when stop loss is hit before take profit.
- SHORT wins when take profit is hit before stop loss.
- SHORT loses when stop loss is hit before take profit.
- If neither level is touched before expiry, the result becomes `EXPIRED` and PnL is calculated from the last available close.
- If candle data is unavailable, the result becomes `NO_DATA`.

No fake results are generated. After 90 saved signals, the summary can show how many were `WIN`, `LOSS`, `EXPIRED`, or `NO_DATA` and calculate the real win rate.
