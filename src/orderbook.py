"""
Step 2: Order Book Imbalance Detection
Measures buy-side vs sell-side depth on Polymarket's order book.
"""

import asyncio
import json
import time
import websockets
from typing import Optional


POLYMARKET_WS = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


def calculate_imbalance(order_book: dict) -> float:
    """
    Measures the ratio of buy-side depth to sell-side depth.
    Values > 1.0 = more buyers than sellers = bullish pressure.

    - Above 1.8: buyers stacking the book (UP signal)
    - 0.55-1.8:  neutral — no trade
    - Below 0.55: sellers dominant (DOWN signal)
    """
    bid_depth = sum(order["size"] for order in order_book["bids"][:10])
    ask_depth = sum(order["size"] for order in order_book["asks"][:10])

    if ask_depth == 0:
        return float("inf")

    return round(bid_depth / ask_depth, 3)


def detect_smart_entry(
    imbalance_history: list,
    threshold: float = 1.8,
    window_seconds: int = 90,
) -> Optional[dict]:
    """
    Smart money enters 30-90 seconds after market open.
    If imbalance spikes during that window, it's a signal.
    """
    early_window = [
        ib
        for ib in imbalance_history
        if 30 <= ib["seconds_since_open"] <= window_seconds
    ]

    if not early_window:
        return None

    max_imbalance = max(ib["ratio"] for ib in early_window)

    if max_imbalance >= threshold:
        return {
            "direction": "UP",
            "strength": max_imbalance,
            "confidence": min(max_imbalance / 2.5, 0.95),
        }
    elif min(ib["ratio"] for ib in early_window) <= 1 / threshold:
        return {
            "direction": "DOWN",
            "strength": 1 / min(ib["ratio"] for ib in early_window),
            "confidence": min(
                (1 / min(ib["ratio"] for ib in early_window)) / 2.5, 0.95
            ),
        }

    return None


async def get_order_book(market: dict) -> dict:
    """
    Subscribe to Polymarket WebSocket for real-time order book data.
    Returns a snapshot with bids and asks.
    """
    token_id = market.get("up_token")  # or down_token depending on direction
    order_book = {"bids": [], "asks": []}

    try:
        async with websockets.connect(POLYMARKET_WS) as ws:
            subscribe_msg = {
                "type": "Market",
                "assets_ids": [market["up_token"], market["down_token"]],
            }
            await ws.send(json.dumps(subscribe_msg))

            # Collect for 3 seconds to get a snapshot
            deadline = time.time() + 3
            while time.time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if data.get("type") == "book" and data.get("asset_id") == token_id:
                        order_book = {
                            "bids": [
                                {"price": float(b[0]), "size": float(b[1])}
                                for b in data.get("bids", [])
                            ],
                            "asks": [
                                {"price": float(a[0]), "size": float(a[1])}
                                for a in data.get("asks", [])
                            ],
                        }
                        break
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        print(f"  [ws] order book error: {e}")

    return order_book
