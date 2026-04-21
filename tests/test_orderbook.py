"""Tests for orderbook module - imbalance calculation and smart entry detection."""

import pytest
from unittest.mock import AsyncMock, patch


def test_calculate_imbalance_bullish():
    """Test imbalance calculation with bullish order book."""
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [{"price": 0.55, "size": 1800}] * 10,
        "asks": [{"price": 0.56, "size": 1000}] * 10,
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == 1.8


def test_calculate_imbalance_bearish():
    """Test imbalance calculation with bearish order book."""
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [{"price": 0.44, "size": 500}] * 10,
        "asks": [{"price": 0.45, "size": 1000}] * 10,
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == 0.5


def test_calculate_imbalance_zero_asks():
    """Test imbalance with no asks (edge case)."""
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [{"price": 0.55, "size": 1000}] * 10,
        "asks": [],
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == float("inf")


def test_calculate_imbalance_zero_bids():
    """Test imbalance with no bids (edge case)."""
    from src.orderbook import calculate_imbalance

    order_book = {
        "bids": [],
        "asks": [{"price": 0.56, "size": 1000}] * 10,
    }
    imbalance = calculate_imbalance(order_book)
    assert imbalance == 0.0


def test_detect_smart_entry_up():
    """Test smart entry detection for UP signal."""
    from src.orderbook import detect_smart_entry

    history = [
        {"seconds_since_open": 45, "ratio": 2.1},
        {"seconds_since_open": 60, "ratio": 2.3},
    ]
    result = detect_smart_entry(history, threshold=1.8)
    assert result is not None
    assert result["direction"] == "UP"
    assert result["strength"] == 2.3


def test_detect_smart_entry_down():
    """Test smart entry detection for DOWN signal."""
    from src.orderbook import detect_smart_entry

    history = [
        {"seconds_since_open": 45, "ratio": 0.4},
        {"seconds_since_open": 70, "ratio": 0.3},
    ]
    result = detect_smart_entry(history, threshold=1.8)
    assert result is not None
    assert result["direction"] == "DOWN"
    # strength = 1 / min_ratio = 1 / 0.3 = 3.333...
    assert result["strength"] == pytest.approx(3.3333, rel=0.01)


def test_detect_smart_entry_none_outside_window():
    """Test that entries outside 30-90s window are ignored."""
    from src.orderbook import detect_smart_entry

    history = [
        {"seconds_since_open": 10, "ratio": 3.0},  # too early
        {"seconds_since_open": 200, "ratio": 3.0},  # too late
    ]
    result = detect_smart_entry(history, threshold=1.8)
    assert result is None


def test_detect_smart_entry_none_below_threshold():
    """Test that weak signals are rejected."""
    from src.orderbook import detect_smart_entry

    history = [
        {"seconds_since_open": 60, "ratio": 1.5},  # below threshold
    ]
    result = detect_smart_entry(history, threshold=1.8)
    assert result is None


@pytest.mark.asyncio
async def test_get_order_book():
    """Test fetching order book from WebSocket."""
    from src.orderbook import get_order_book

    mock_market = {"up_token": "token_123", "down_token": "token_456"}

    # Mock websockets.connect
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock(
        return_value='{"type": "book", "asset_id": "token_123", "bids": [[0.55, 1000]], "asks": [[0.56, 500]]}'
    )
    mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
    mock_ws.__aexit__ = AsyncMock()

    with patch("websockets.connect", return_value=mock_ws):
        order_book = await get_order_book(mock_market)
        assert "bids" in order_book
        assert "asks" in order_book
