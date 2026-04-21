"""
Market scanning — find and track 5-minute BTC markets on Polymarket.
"""

import asyncio
import time
from py_clob_client.client import ClobClient
from .config import POLYMARKET_API_KEY, POLYMARKET_API_SECRET, POLYMARKET_API_PASSPHRASE


def get_clob_client() -> ClobClient:
    return ClobClient(
        host="https://clob.polymarket.com",
        key=POLYMARKET_API_KEY,
        secret=POLYMARKET_API_SECRET,
        passphrase=POLYMARKET_API_PASSPHRASE,
        chain_id=137,
    )


async def get_next_market() -> dict:
    """
    Poll for the next opening 5-minute BTC market.
    Returns market metadata including price_to_beat, tokens, and resolution_time.
    """
    client = get_clob_client()

    while True:
        try:
            markets = client.get_markets()
            for market in markets.get("data", []):
                # Filter for 5-min BTC markets that are about to open or just opened
                if (
                    "BTC" in market.get("question", "")
                    and "5" in market.get("question", "")
                    and market.get("active", False)
                    and market.get("seconds_delay", 999) < 10
                ):
                    tokens = market.get("tokens", [])
                    up_token = next((t["token_id"] for t in tokens if t["outcome"] == "Yes"), None)
                    down_token = next((t["token_id"] for t in tokens if t["outcome"] == "No"), None)

                    return {
                        "question": market["question"],
                        "price_to_beat": float(market.get("price_to_beat", 0)),
                        "up_token": up_token,
                        "down_token": down_token,
                        "resolution_time": market.get("end_date_iso", 0),
                        "market_id": market["condition_id"],
                        "elapsed_seconds": 0,
                        "open_time": time.time(),
                        "price": 0.50,  # default entry price estimate
                        "best_ask": {"up": 0.50, "down": 0.50},
                    }
        except Exception as e:
            print(f"  [market] scan error: {e}")

        await asyncio.sleep(5)


async def wait_for_entry_window(market: dict):
    """Wait until we're 60 seconds past market open."""
    elapsed = time.time() - market.get("open_time", time.time())
    if elapsed < 60:
        wait = 60 - elapsed
        print(f"  waiting {wait:.0f}s for entry window...")
        await asyncio.sleep(wait)
    market["elapsed_seconds"] = time.time() - market.get("open_time", time.time())


async def wait_for_next_market(market: dict):
    """Wait until current market resolves, then return."""
    resolution_time = market.get("resolution_time", 0)
    if isinstance(resolution_time, str):
        from datetime import datetime

        resolution_time = datetime.fromisoformat(resolution_time.replace("Z", "+00:00")).timestamp()

    remaining = resolution_time - time.time()
    if remaining > 0:
        print(f"  waiting {remaining:.0f}s for next market...")
        await asyncio.sleep(max(0, remaining + 2))
