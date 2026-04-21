"""Tests for market module - market scanning and timing."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import time


def test_get_clob_client():
    """Test CLOB client initialization."""
    from src.market import get_clob_client

    with patch("src.market.ClobClient") as mock_clob:
        get_clob_client()
        assert mock_clob.called


@pytest.mark.asyncio
async def test_get_next_market_finds_btc_market():
    """Test finding next BTC 5-minute market."""
    from src.market import get_next_market

    mock_client = MagicMock()
    mock_client.get_markets.return_value = {
        "data": [
            {
                "question": "Will BTC be above $105,000 at 12:05 PM?",
                "active": True,
                "seconds_delay": 5,
                "price_to_beat": 105000,
                "tokens": [
                    {"token_id": "token_up", "outcome": "Yes"},
                    {"token_id": "token_down", "outcome": "No"},
                ],
                "condition_id": "market_123",
                "end_date_iso": "2024-01-01T12:05:00Z",
            }
        ]
    }

    with patch("src.market.get_clob_client", return_value=mock_client):
        market = await get_next_market()

        assert "BTC" in market["question"]
        assert market["up_token"] == "token_up"
        assert market["down_token"] == "token_down"
        assert market["price_to_beat"] == 105000


@pytest.mark.asyncio
async def test_get_next_market_retries_on_error():
    """Test retry logic when market scan fails."""
    from src.market import get_next_market

    mock_client = MagicMock()
    mock_client.get_markets.side_effect = [
        Exception("API error"),
        {
            "data": [
                {
                    "question": "Will BTC be above $105,000 at 12:05 PM?",
                    "active": True,
                    "seconds_delay": 5,
                    "price_to_beat": 105000,
                    "tokens": [
                        {"token_id": "token_up", "outcome": "Yes"},
                        {"token_id": "token_down", "outcome": "No"},
                    ],
                    "condition_id": "market_123",
                    "end_date_iso": "2024-01-01T12:05:00Z",
                }
            ]
        },
    ]

    with (
        patch("src.market.get_clob_client", return_value=mock_client),
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        market = await get_next_market()
        assert market is not None


@pytest.mark.asyncio
async def test_wait_for_entry_window_already_passed():
    """Test wait_for_entry_window when 60s already elapsed."""
    from src.market import wait_for_entry_window

    market = {"open_time": time.time() - 90}  # 90s ago

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await wait_for_entry_window(market)

        # Should not wait if already past 60s
        assert not mock_sleep.called
        assert market["elapsed_seconds"] >= 90


@pytest.mark.asyncio
async def test_wait_for_entry_window_needs_wait():
    """Test wait_for_entry_window when <60s elapsed."""
    from src.market import wait_for_entry_window

    market = {"open_time": time.time() - 30}  # 30s ago

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await wait_for_entry_window(market)

        # Should wait ~30s to reach 60s
        assert mock_sleep.called
        wait_time = mock_sleep.call_args[0][0]
        assert 20 < wait_time < 40


@pytest.mark.asyncio
async def test_wait_for_next_market_with_timestamp():
    """Test waiting for next market with timestamp."""
    from src.market import wait_for_next_market

    market = {"resolution_time": time.time() + 100}

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await wait_for_next_market(market)

        # Should wait for resolution + 2s buffer
        assert mock_sleep.called
        wait_time = mock_sleep.call_args[0][0]
        assert 90 < wait_time < 110


@pytest.mark.asyncio
async def test_wait_for_next_market_with_iso_string():
    """Test waiting for next market with ISO timestamp string."""
    from src.market import wait_for_next_market
    from datetime import datetime, timedelta, timezone

    future_time = datetime.now(timezone.utc) + timedelta(seconds=100)
    iso_string = future_time.isoformat().replace("+00:00", "Z")

    market = {"resolution_time": iso_string}

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await wait_for_next_market(market)

        assert mock_sleep.called
        wait_time = mock_sleep.call_args[0][0]
        assert 90 < wait_time < 110


@pytest.mark.asyncio
async def test_wait_for_next_market_already_past():
    """Test waiting when resolution time is in the past."""
    from src.market import wait_for_next_market

    market = {"resolution_time": time.time() - 100}  # Past

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await wait_for_next_market(market)

        # When resolution time is in past (remaining <= 0), sleep is not called
        assert not mock_sleep.called
