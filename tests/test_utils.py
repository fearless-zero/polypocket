"""Tests for utils module - Kelly sizing and formatters."""

import pytest


def test_kelly_size_positive():
    """Test Kelly sizing with positive edge."""
    from src.utils import kelly_size

    size = kelly_size(confidence=0.71, price=0.50, bankroll=2000)
    assert size > 0
    assert size < 300  # Should not bet entire bankroll (quarter-Kelly with caps)


def test_kelly_size_low_confidence():
    """Test that lower confidence results in smaller position."""
    from src.utils import kelly_size

    size_low = kelly_size(confidence=0.52, price=0.50, bankroll=2000)
    size_high = kelly_size(confidence=0.85, price=0.50, bankroll=2000)

    assert size_low < size_high


def test_kelly_size_no_edge():
    """Test Kelly sizing with no edge (50% confidence)."""
    from src.utils import kelly_size

    size = kelly_size(confidence=0.50, price=0.50, bankroll=2000)
    assert size == 0  # No bet when no edge


def test_kelly_size_capped_at_25_percent():
    """Test that Kelly is capped at 25% of bankroll."""
    from src.utils import kelly_size

    # Even with 99% confidence, should cap at 25% of bankroll
    size = kelly_size(confidence=0.99, price=0.01, bankroll=2000)
    max_position = 2000 * 0.25 * 0.25  # 25% cap * quarter-Kelly

    assert size <= max_position / 0.01  # shares = position_value / price


def test_kelly_size_different_prices():
    """Test Kelly sizing at different price points."""
    from src.utils import kelly_size

    size_cheap = kelly_size(confidence=0.70, price=0.30, bankroll=2000)
    size_expensive = kelly_size(confidence=0.70, price=0.70, bankroll=2000)

    # Cheaper price should result in more shares for same bankroll allocation
    assert size_cheap > size_expensive


def test_kelly_size_zero_confidence():
    """Test Kelly sizing with zero confidence."""
    from src.utils import kelly_size

    size = kelly_size(confidence=0.0, price=0.50, bankroll=2000)
    assert size == 0


def test_kelly_size_bankroll_scaling():
    """Test that position scales with bankroll."""
    from src.utils import kelly_size

    size_small = kelly_size(confidence=0.70, price=0.50, bankroll=1000)
    size_large = kelly_size(confidence=0.70, price=0.50, bankroll=4000)

    assert size_large > size_small
    assert size_large / size_small == pytest.approx(4.0, rel=0.01)


def test_format_pnl_positive():
    """Test P&L formatting for profit."""
    from src.utils import format_pnl

    assert format_pnl(123.45) == "+$123.45"
    assert format_pnl(0.01) == "+$0.01"


def test_format_pnl_negative():
    """Test P&L formatting for loss."""
    from src.utils import format_pnl

    assert format_pnl(-123.45) == "-$123.45"
    assert format_pnl(-0.01) == "-$0.01"


def test_format_pnl_zero():
    """Test P&L formatting for breakeven."""
    from src.utils import format_pnl

    assert format_pnl(0.0) == "+$0.00"
