"""Tests for execution module - order placement and timing."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_place_limit_order_success():
    """Test successful limit order placement."""
    from src.execution import place_limit_order

    mock_client = MagicMock()
    mock_order = {"orderID": "test_order_123"}
    mock_response = {"orderID": "test_order_123", "status": "live"}
    mock_client.create_order.return_value = mock_order
    mock_client.post_order.return_value = mock_response

    with patch("src.execution.get_clob_client", return_value=mock_client):
        order = await place_limit_order(
            token_id="token_123",
            price=0.50,
            size=100,
            side="buy",
        )

        assert order is not None
        assert order["orderID"] == "test_order_123"
        assert order["status"] == "live"


@pytest.mark.asyncio
async def test_execute_trade_within_window(mock_market, mock_polymarket_client):
    """Test trade execution within valid window (60-180s)."""
    from src.execution import execute_trade

    signal = {
        "direction": "UP",
        "size": 100,
        "confidence": 0.75,
    }

    # Set market elapsed_seconds to be 90 (within window)
    mock_market["elapsed_seconds"] = 90

    with patch(
        "src.execution.place_limit_order",
        new=AsyncMock(return_value={"orderID": "test_123", "status": "live"}),
    ):
        position = await execute_trade(signal, mock_market)

        assert position is not None
        assert position["direction"] == "UP"
        assert position["token_id"] == mock_market["up_token"]
        assert position["size"] == 100


@pytest.mark.asyncio
async def test_execute_trade_too_early(mock_market):
    """Test that trade is delayed if market opened <60s ago."""
    from src.execution import execute_trade

    signal = {"direction": "UP", "size": 100, "confidence": 0.75}

    # Market just opened (too early)
    mock_market["elapsed_seconds"] = 10

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        with patch(
            "src.execution.place_limit_order",
            new=AsyncMock(return_value={"orderID": "test", "status": "live"}),
        ):
            await execute_trade(signal, mock_market)

            # Should wait for remaining time to reach 60s
            assert mock_sleep.called
            sleep_time = mock_sleep.call_args[0][0]
            assert 40 < sleep_time < 60


@pytest.mark.asyncio
async def test_execute_trade_too_late(mock_market):
    """Test that trade is rejected if >180s since market open."""
    from src.execution import execute_trade

    signal = {"direction": "UP", "size": 100, "confidence": 0.75}

    # Market opened 200 seconds ago (too late)
    mock_market["elapsed_seconds"] = 200

    position = await execute_trade(signal, mock_market)
    assert position is None


@pytest.mark.asyncio
async def test_execute_trade_order_failed(mock_market):
    """Test handling of failed order placement."""
    from src.execution import execute_trade

    signal = {"direction": "UP", "size": 100, "confidence": 0.75}
    mock_market["elapsed_seconds"] = 90

    # Order fails
    with patch("src.execution.place_limit_order", new=AsyncMock(return_value={"status": "failed"})):
        position = await execute_trade(signal, mock_market)
        assert position is None


@pytest.mark.asyncio
async def test_execute_trade_down_direction(mock_market):
    """Test execution for DOWN signal."""
    from src.execution import execute_trade

    signal = {"direction": "DOWN", "size": 100, "confidence": 0.75}
    mock_market["elapsed_seconds"] = 90

    with patch(
        "src.execution.place_limit_order",
        new=AsyncMock(return_value={"orderID": "test_123", "status": "live"}),
    ):
        position = await execute_trade(signal, mock_market)

        assert position is not None
        assert position["direction"] == "DOWN"
        assert position["token_id"] == mock_market["down_token"]


def test_get_clob_client():
    """Test CLOB client initialization."""
    from src.execution import get_clob_client

    with patch("src.execution.ClobClient") as mock_clob:
        get_clob_client()
        assert mock_clob.called
