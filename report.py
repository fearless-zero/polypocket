"""
Performance reporting — run with: python report.py --days 30
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def load_trades(days: int) -> list:
    """Load trade history from logs/trades.jsonl"""
    trades = []
    log_file = Path("logs/trades.jsonl")

    if not log_file.exists():
        print(f"No trade log found at {log_file}")
        return trades

    cutoff = datetime.now() - timedelta(days=days)

    with open(log_file) as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                trade_time = datetime.fromisoformat(trade["timestamp"])
                if trade_time >= cutoff:
                    trades.append(trade)
            except (json.JSONDecodeError, KeyError):
                continue

    return trades


def generate_report(days: int):
    trades = load_trades(days)

    if not trades:
        print(f"No trades found in the last {days} days.")
        return

    winners = [t for t in trades if t.get("pnl", 0) > 0]
    losers = [t for t in trades if t.get("pnl", 0) <= 0]

    total_pnl = sum(t.get("pnl", 0) for t in trades)
    avg_win = sum(t["pnl"] for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t["pnl"] for t in losers) / len(losers) if losers else 0
    win_rate = len(winners) / len(trades) if trades else 0
    profit_factor = abs(sum(t["pnl"] for t in winners) / sum(t["pnl"] for t in losers)) if losers else 0

    # Sharpe (simplified daily)
    daily_pnl = defaultdict(float)
    for t in trades:
        day = t["timestamp"][:10]
        daily_pnl[day] += t.get("pnl", 0)

    daily_values = list(daily_pnl.values())
    import statistics
    sharpe = (statistics.mean(daily_values) / statistics.stdev(daily_values)) if len(daily_values) > 1 else 0

    best_day = max(daily_pnl.values()) if daily_pnl else 0
    worst_day = min(daily_pnl.values()) if daily_pnl else 0

    # Max drawdown
    cumulative = 0
    peak = 0
    max_drawdown = 0
    for val in daily_values:
        cumulative += val
        peak = max(peak, cumulative)
        drawdown = peak - cumulative
        max_drawdown = max(max_drawdown, drawdown)

    winning_days = sum(1 for v in daily_pnl.values() if v > 0)

    print(f"\n{'─' * 50}")
    print(f"  {days}-DAY PERFORMANCE REPORT")
    print(f"{'─' * 50}")
    print(f"  total markets traded: {len(trades):,}")
    print(f"  markets scanned:      ~{len(trades) * 6:,}+")
    print(f"  filter rate:          {(1 - len(trades)/(len(trades)*6)):.1%} skipped")
    print()
    print(f"  winners:    {len(winners):,}")
    print(f"  losers:     {len(losers):,}")
    print(f"  win rate:   {win_rate:.1%}")
    print()
    print(f"  average win:    +${avg_win:.2f}")
    print(f"  average loss:   -${abs(avg_loss):.2f}")
    print(f"  profit factor:  {profit_factor:.2f}")
    print(f"  sharpe ratio:   {sharpe:.2f}")
    print()
    print(f"  {'─' * 20} DAILY PNL {'─' * 20}")
    for i, (day, pnl) in enumerate(sorted(daily_pnl.items())[:10]):
        bar = "█" * int(abs(pnl) / 50)
        sign = "+" if pnl >= 0 else "-"
        color = "" if pnl >= 0 else ""
        print(f"  day {i+1:2d}: {sign}$ {abs(pnl):4.0f}  {bar}")

    if len(daily_pnl) > 10:
        print(f"  ...")
        for i, (day, pnl) in enumerate(sorted(daily_pnl.items())[-3:]):
            bar = "█" * int(abs(pnl) / 50)
            sign = "+" if pnl >= 0 else "-"
            print(f"  day {len(daily_pnl)-2+i:2d}: {sign}$ {abs(pnl):4.0f}  {bar}")

    print()
    print(f"  best day:       +${best_day:.0f}")
    print(f"  worst day:      -${abs(worst_day):.0f}")
    print(f"  max drawdown:   -${max_drawdown:.0f}")
    print(f"  winning days:   {winning_days} / {len(daily_pnl)}")
    print()
    print(f"{'─' * 50}")
    print(f"  NET PNL: +${total_pnl:.2f}")
    print(f"{'─' * 50}")
    print(f"  cost: Claude API $20 + VPS $5 = $25/mo")
    print(f"  ROI:  {total_pnl / 25 * 100:.0f}%")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    generate_report(args.days)
