# polymarket-5min

Polymarket 5-minute BTC trading bot. Trades UP/DOWN markets using dual-signal confirmation:
multi-source price divergence (Binance + Coinbase vs Chainlink) and order book imbalance.

**Strategy summary:** 71% win rate, early exit at 75c, skip 85% of windows.

---

## Stack

| Tool | Cost | What It Does |
|---|---|---|
| VPS (Hetzner) | $5/mo | Runs the engine 24/7 |
| Polymarket WebSocket | Free | Real-time order book data |
| Binance API | Free | BTC price feed |
| Coinbase API | Free | BTC price feed (cross-reference) |
| Chainlink feed | Free | On-chain price (resolution source) |

---

## Setup

```bash
# 1. Clone and install
git clone <this-repo>
cd polymarket-5min
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Fill in your Polymarket API keys (get from polymarket.com/profile)

# 3. Run the engine
python -m src.engine --mode live --session overnight

# 4. Generate performance report
python report.py --days 30

# 5. Analyze order book patterns (requires historical data)
python analyze_orderbook.py --windows 2000
```

---

## Architecture

```
engine.py           — main loop, one lifecycle per 5-min window
├── market.py       — find next opening BTC market
├── prices.py       — fetch BTC from Binance + Coinbase + Chainlink in parallel
├── orderbook.py    — Polymarket WebSocket order book + imbalance calculation
├── signals.py      — combine both signals, kill 85% of windows
├── execution.py    — limit order placement, 60-180s timing window
└── monitor.py      — position monitoring, 3 exit conditions
```

## Signal Logic

**Step 1 — Price Divergence:** Both Binance and Coinbase must be >$50 above/below the Polymarket Price to Beat.

**Step 2 — Order Book Imbalance:** Bid/ask depth ratio must be >1.8 (UP) or <0.55 (DOWN) in the 30-90s window after open.

**Step 3 — Combined Signal:** Both must agree. If they disagree, skip (47% win rate = worse than random).

**Step 4 — Entry Timing:** Place limit order 60-180s after market open. Before 60s = too noisy. After 180s = can't exit if wrong.

**Step 5 — Early Exit:** Sell at 75c (profit target) or 35c (stop loss). Don't hold to resolution — on-chain settlement lag creates exit risk in the last 60 seconds.

---

## Referenced repos
- https://github.com/warproxxx/poly_data — historical trade data for backtesting
- https://github.com/Polymarket/polymarket-cli — market scanning and order placement
- https://github.com/Polymarket/agents — agent framework and LLM integration
- https://github.com/KaustubhPatange/polymarket-trade-engine — 5-minute market engine architecture

---

**DYOR. This is not financial advice. You will have losing days.**
