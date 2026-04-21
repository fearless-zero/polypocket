"""Tests for monitor module - position monitoring and exits."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import time


@pytest.mark.asyncio
async def test_monitor_position_profit_target(mock_position):
    """Test exit at profit target (75¢)."""
    from src.monitor import monitor_position

    mock_position["market"]["resolution_time"] = time.time() + 200

    with (
        patch("src.monitor.get_current_price", return_value=0.76),
        patch("src.monitor.sell_shares", new=AsyncMock(return_value={"status": "filled"})),
    ):
        result = await monitor_position(mock_position, mock_position["market"])

        assert result["exit"] == "PROFIT_TARGET"
        assert result["pnl"] > 0
        assert result["exit_price"] == 0.76


@pytest.mark.asyncio
async def test_monitor_position_stop_loss(mock_position):
    """Test exit at stop loss (35¢)."""
    from src.monitor import monitor_position

    mock_position["market"]["resolution_time"] = time.time() + 200

    with (
        patch("src.monitor.get_current_price", return_value=0.33),
        patch("src.monitor.sell_shares", new=AsyncMock(return_value={"status": "filled"})),
    ):
        result = await monitor_position(mock_position, mock_position["market"])

        assert result["exit"] == "STOP_LOSS"
        assert result["pnl"] < 0
        assert result["exit_price"] == 0.33


@pytest.mark.asyncio
async def test_monitor_position_time_exit(mock_position):
    """Test hold to resolution when <60s remain."""
    from src.monitor import monitor_position

    # Set resolution time to be very soon (to trigger time exit quickly)
    mock_position["market"]["resolution_time"] = time.time() + 0.1

    with patch("src.monitor.get_current_price", return_value=0.55):
        with patch("asyncio.sleep", new=AsyncMock()):  # Speed up the loop
            result = await monitor_position(mock_position, mock_position["market"])

            # When time is <60s, it holds to resolution
            assert result["exit"] == "HOLD_TO_RESOLUTION"


@pytest.mark.asyncio
async def test_get_current_price():
    """Test current price fetching."""
    from src.monitor import get_current_price

    mock_client = MagicMock()
    mock_client.get_order_book.return_value = {
        "bids": [{"price": 0.54}],
        "asks": [{"price": 0.56}],
    }

    with patch("src.monitor.get_clob_client", return_value=mock_client):
        price = await get_current_price("token_123")

        # Mid price = (best_bid + best_ask) / 2
        assert price == 0.55


@pytest.mark.asyncio
async def test_get_current_price_empty_book():
    """Test fallback when order book is empty."""
    from src.monitor import get_current_price

    mock_client = MagicMock()
    mock_client.get_order_book.return_value = {
        "bids": [],
        "asks": [],
    }

    with patch("src.monitor.get_clob_client", return_value=mock_client):
        price = await get_current_price("token_123")

        # Fallback to 0.5
        assert price == 0.5


@pytest.mark.asyncio
async def test_sell_shares():
    """Test share selling."""
    from src.monitor import sell_shares

    position = {
        "token_id": "token_123",
        "size": 100,
    }

    with patch("src.monitor.place_limit_order", new=AsyncMock(return_value={"status": "filled"})):
        order = await sell_shares(position, 0.75)

        assert order["status"] == "filled"
