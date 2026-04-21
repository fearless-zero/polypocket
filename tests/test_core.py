"""
Tests for polypocket — mocks all external I/O.
"""

import pytest
from unittest.mock import patch, MagicMock


# ── signals ──────────────────────────────────────────────────────────────────

def test_should_trade_both_signals_up():
    from src.signals import should_trade

    price_data = {"binance": 105100, "coinbase": 105120, "chainlink": 105000}
    order_book = {
        "bids": [{"price": 0.55, "size": 1000}] * 10,
        "asks": [{"price": 0.56, "size": 400}] * 10,
    }
    market = {"price_to_beat": 105000, "price": 0.50, "best_ask": {"up": 0.50, "down": 0.50}}

    signal = should_trade(price_data, order_book, market)
    assert signal is not None
    assert signal["direction"] == "UP"
    assert 0 < signal["confidence"] <= 0.95


def test_should_trade_both_signals_down():
    from src.signals import should_trade

    price_data = {"binance": 104900, "coinbase": 104880, "chainlink": 105000}
    order_book = {
        "bids": [{"price": 0.44, "size": 200}] * 10,
        "asks": [{"price": 0.45, "size": 1000}] * 10,
    }
    market = {"price_to_beat": 105000, "price": 0.50, "best_ask": {"up": 0.50, "down": 0.50}}

    signal = should_trade(price_data, order_book, market)
    assert signal is not None
    assert signal["direction"] == "DOWN"


def test_should_trade_no_signal_when_exchanges_disagree():
    from src.signals import should_trade

    # Binance above, Coinbase below — no clear divergence
    price_data = {"binance": 105100, "coinbase": 104900, "chainlink": 105000}
    order_book = {
        "bids": [{"price": 0.55, "size": 1000}] * 10,
        "asks": [{"price": 0.56, "size": 400}] * 10,
    }
    market = {"price_to_beat": 105000, "price": 0.50, "best_ask": {"up": 0.50, "down": 0.50}}

    signal = should_trade(price_data, order_book, market)
    assert signal is None


def test_should_trade_no_signal_when_book_neutral():
    from src.signals import should_trade

    # Both exchanges agree UP, but book is neutral
    price_data = {"binance": 105100, "coinbase": 105120, "chainlink": 105000}
    order_book = {
        "bids": [{"price": 0.50, "size": 500}] * 10,
        "asks": [{"price": 0.51, "size": 500}] * 10,
    }
    market = {"price_to_beat": 105000, "price": 0.50, "best_ask": {"up": 0.50, "down": 0.50}}

    signal = should_trade(price_data, order_book, market)
    assert signal is None


# ── orderbook ─────────────────────────────────────────────────────────────────

def test_calculate_imbalance_bullish():
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [{"price": 0.55, "size": 1800}] * 10,
        "asks": [{"price": 0.56, "size": 1000}] * 10,
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == 1.8


def test_calculate_imbalance_bearish():
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [{"price": 0.44, "size": 500}] * 10,
        "asks": [{"price": 0.45, "size": 1000}] * 10,
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == 0.5


def test_calculate_imbalance_zero_asks():
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [{"price": 0.55, "size": 1000}] * 10,
        "asks": [],
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == float("inf")


def test_detect_smart_entry_up():
    from src.orderbook import detect_smart_entry

    history = [
        {"seconds_since_open": 45, "ratio": 2.1},
        {"seconds_since_open": 60, "ratio": 2.3},
    ]
    result = detect_smart_entry(history, threshold=1.8)
    assert result is not None
    assert result["direction"] == "UP"
    assert result["strength"] == 2.3


def test_detect_smart_entry_none_outside_window():
    from src.orderbook import detect_smart_entry

    history = [
        {"seconds_since_open": 10, "ratio": 3.0},  # too early
        {"seconds_since_open": 200, "ratio": 3.0},  # too late
    ]
    result = detect_smart_entry(history, threshold=1.8)
    assert result is None


# ── utils ─────────────────────────────────────────────────────────────────────

def test_kelly_size_positive():
    from src.utils import kelly_size

    size = kelly_size(confidence=0.71, price=0.50, bankroll=2000)
    assert size > 0
    assert size < 200  # sanity check — not betting entire bankroll


def test_kelly_size_low_confidence():
    from src.utils import kelly_size

    size_low = kelly_size(confidence=0.52, price=0.50, bankroll=2000)
    size_high = kelly_size(confidence=0.85, price=0.50, bankroll=2000)
    assert size_low < size_high
