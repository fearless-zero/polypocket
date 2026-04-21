"""
Step 4: Execution Timing
Sweet spot: 60-180 seconds after market open.
- Not too early (signal might reverse)
- Not too late (can't fill, can't exit)
"""

import asyncio
from typing import Optional

from py_clob_client.client import ClobClient
from .config import POLYMARKET_API_KEY, POLYMARKET_API_SECRET, POLYMARKET_API_PASSPHRASE


def get_clob_client() -> ClobClient:
    return ClobClient(
        host="https://clob.polymarket.com",
        key=POLYMARKET_API_KEY,
        secret=POLYMARKET_API_SECRET,
        passphrase=POLYMARKET_API_PASSPHRASE,
        chain_id=137,  # Polygon
    )


async def place_limit_order(token_id: str, price: float, size: float, side: str) -> dict:
    """Place a limit order via Polymarket CLOB API."""
    client = get_clob_client()

    order_args = {
        "token_id": token_id,
        "price": price,
        "size": size,
        "side": side,  # "buy" or "sell"
    }

    order = client.create_order(order_args)
    resp = client.post_order(order)
    return resp


async def execute_trade(signal: dict, market: dict) -> Optional[dict]:
    """
    Place order at optimal timing.
    Sweet spot: 60-180 seconds after market open.
    """
    seconds_since_open = market["elapsed_seconds"]

    # Too early — signal might reverse
    if seconds_since_open < 60:
        await asyncio.sleep(60 - seconds_since_open)  # wait for confirmation

    # Too late — can't exit if wrong
    if seconds_since_open > 180:
        return None

    # Place limit order at current best price (always buy shares)
    token_id = (
        market["up_token"] if signal["direction"] == "UP" else market["down_token"]
    )

    order = await place_limit_order(
        token_id=token_id,
        price=market["best_ask"][signal["direction"].lower()],
        size=signal["size"],
    )

    if order is None or order.get("status") == "failed":
        return None

    return {
        "token_id": token_id,
        "direction": signal["direction"],
        "entry_price": market["best_ask"][signal["direction"].lower()],
        "size": signal["size"],
        "order_id": order.get("orderID"),
        "market": market,
    }
