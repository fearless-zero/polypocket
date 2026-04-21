"""
Utility functions — Kelly criterion sizing and helpers.
"""


def kelly_size(confidence: float, price: float, bankroll: float = 2000.0) -> float:
    """
    Kelly criterion position sizing.
    f* = (bp - q) / b
    where b = odds, p = win probability, q = 1-p

    For a binary market paying $1:
    - If we buy at price p, we win (1-p) or lose p
    - b = (1 - price) / price
    """
    p = confidence  # estimated win probability
    q = 1 - p
    b = (1 - price) / price if price < 1 else 1

    kelly_fraction = (b * p - q) / b
    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # cap at 25% of bankroll

    # Quarter-Kelly for safety
    position_value = bankroll * kelly_fraction * 0.25
    shares = position_value / price

    return round(shares, 2)


def format_pnl(pnl: float) -> str:
    if pnl >= 0:
        return f"+${pnl:.2f}"
    else:
        return f"-${abs(pnl):.2f}"
