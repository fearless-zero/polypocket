"""
Step 5: The Exit (Before Resolution)
Three exit conditions — never hold to resolution blindly.

Why exit early?
On-chain settlement lag: if you buy with 90 seconds left and it goes wrong,
you might not be able to sell because shares haven't settled yet.
Early exit takes 60-70% of potential profit but eliminates that risk.
"""

import asyncio
import time
from typing import Optional

from .execution import place_limit_order, get_clob_client


async def get_current_price(token_id: str) -> float:
    """Get the current mid price for a token."""
    client = get_clob_client()
    book = client.get_order_book(token_id)
    if book and book.get("bids") and book.get("asks"):
        best_bid = float(book["bids"][0]["price"])
        best_ask = float(book["asks"][0]["price"])
        return (best_bid + best_ask) / 2
    return 0.5  # fallback


async def sell_shares(position: dict, current_price: float) -> dict:
    """Sell position at current market price."""
    client = get_clob_client()

    order = await place_limit_order(
        token_id=position["token_id"],
        price=current_price,
        size=position["size"],
        side="sell",
    )
    return order


async def monitor_position(position: dict, market: dict) -> dict:
    """
    Monitor an open position and exit on one of three conditions:

    1. Profit target: sell when shares hit 75c+ (entered ~48-50c)
    2. Stop loss: sell if shares drop below 35c
    3. Time exit: if <60 seconds remain, hold to resolution
    """
    entry_price = position["entry_price"]

    while True:
        current_price = await get_current_price(position["token_id"])
        time_remaining = market["resolution_time"] - time.time()

        # Exit 1: Profit target
        if current_price >= 0.75:
            await sell_shares(position, current_price)
            pnl = (current_price - entry_price) * position["size"]
            return {"exit": "PROFIT_TARGET", "pnl": pnl, "exit_price": current_price}

        # Exit 2: Stop loss
        if current_price <= 0.35:
            await sell_shares(position, current_price)
            pnl = (current_price - entry_price) * position["size"]
            return {"exit": "STOP_LOSS", "pnl": pnl, "exit_price": current_price}

        # Exit 3: Time — hold to resolution
        if time_remaining < 60:
            return {"exit": "HOLD_TO_RESOLUTION", "pnl": "pending"}

        await asyncio.sleep(2)
