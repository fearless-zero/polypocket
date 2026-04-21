"""
Polymarket 5-Minute BTC Trading Bot
Main engine loop - one market lifecycle per 5-minute window.
"""

import asyncio
import argparse
from datetime import datetime

from .prices import get_prices
from .orderbook import get_order_book
from .signals import should_trade
from .execution import execute_trade
from .monitor import monitor_position
from .market import get_next_market, wait_for_entry_window, wait_for_next_market


async def run_engine(mode: str = "live", session: str = "default"):
    """
    Main loop. One market lifecycle per 5-minute window.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] engine started — scanning 5-min BTC markets")

    bankroll = 2000.0
    daily_pnl = 0.0
    trades_today = 0

    while True:
        market = await get_next_market()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] New market: {market['question']}")
        print(f"  Price to Beat: ${market['price_to_beat']:,.2f}")

        # Wait for the entry window (60 seconds after open)
        await wait_for_entry_window(market)

        # Collect signals
        prices = await get_prices()
        order_book = await get_order_book(market)
        signal = should_trade(prices, order_book, market)

        if signal is None:
            print("  SKIP — no signal convergence")
            await wait_for_next_market(market)
            continue

        # Execute
        position = await execute_trade(signal, market)
        if position is None:
            print("  SKIP — execution window missed")
            await wait_for_next_market(market)
            continue

        # Monitor and exit
        result = await monitor_position(position, market)
        daily_pnl += result.get("pnl", 0)
        trades_today += 1

        print(f"  {result['exit']} | PNL: ${result['pnl']:.2f}")
        print(f"  Daily: ${daily_pnl:.2f} | Trades: {trades_today}")

        # Update bankroll
        bankroll += result.get("pnl", 0)

        await wait_for_next_market(market)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket 5-min BTC trading engine")
    parser.add_argument("--mode", default="live", choices=["live", "paper", "backtest"])
    parser.add_argument("--session", default="default")
    args = parser.parse_args()

    asyncio.run(run_engine(mode=args.mode, session=args.session))
