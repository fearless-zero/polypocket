"""
Step 3: The Signal Combiner
Only trade when BOTH signals agree. Kill everything else.

- Price divergence alone: 63% win rate
- Order book imbalance alone: 58% win rate
- Both together: 71% win rate
- Signals disagree: 47% — worse than random
"""

from .orderbook import calculate_imbalance
from .utils import kelly_size


def should_trade(price_data: dict, order_book: dict, market: dict) -> dict | None:
    """
    Only trade when both signals agree.
    Kill everything else.
    """
    # Signal 1: Price divergence
    # Both Binance and Coinbase must agree on direction vs the Price to Beat
    binance_delta = price_data["binance"] - market["price_to_beat"]
    coinbase_delta = price_data["coinbase"] - market["price_to_beat"]

    exchanges_agree = (
        (binance_delta > 50 and coinbase_delta > 50) or
        (binance_delta < -50 and coinbase_delta < -50)
    )

    if not exchanges_agree:
        return None  # no clear divergence

    direction = "UP" if binance_delta > 0 else "DOWN"

    # Signal 2: Order book confirmation
    imbalance = calculate_imbalance(order_book)
    book_confirms = (
        (direction == "UP" and imbalance > 1.8) or
        (direction == "DOWN" and imbalance < 0.55)
    )

    if not book_confirms:
        return None  # divergence without book support = trap

    # Both signals agree — calculate confidence and size
    confidence = min(0.95, 0.6 + abs(binance_delta) / 500 + abs(imbalance - 1.0) / 10)

    return {
        "direction": direction,
        "confidence": round(confidence, 3),
        "size": kelly_size(confidence, market["price"], bankroll=2000),
        "binance_delta": binance_delta,
        "coinbase_delta": coinbase_delta,
        "imbalance": imbalance,
    }
