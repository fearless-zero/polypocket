"""
Test fixtures and configuration for polypocket tests.
Mocks all external I/O (Polymarket, Binance, Coinbase, Chainlink).
"""

import os
from unittest.mock import AsyncMock, MagicMock
import pytest

# Set test environment
os.environ["POLYMARKET_API_KEY"] = "test_key"
os.environ["POLYMARKET_API_SECRET"] = "test_secret"
os.environ["POLYMARKET_API_PASSPHRASE"] = "test_passphrase"
os.environ["CHAINLINK_RPC"] = "https://polygon-rpc.com"
os.environ["BANKROLL"] = "2000"


@pytest.fixture
def mock_polymarket_client():
    """Mock Polymarket CLOB client."""
    client = MagicMock()
    client.get_order_book = MagicMock(
        return_value={
            "bids": [{"price": 0.55, "size": 1000}] * 10,
            "asks": [{"price": 0.56, "size": 400}] * 10,
        }
    )
    client.create_order = AsyncMock(
        return_value={
            "orderID": "test_order_123",
            "status": "live",
            "price": 0.50,
            "size": 100,
        }
    )
    client.cancel_order = AsyncMock(return_value={"status": "cancelled"})
    return client


@pytest.fixture
def mock_market():
    """Mock 5-minute BTC market."""
    return {
        "id": "test_market_123",
        "question": "Will BTC be above $105,000 at 12:05 PM UTC?",
        "price_to_beat": 105000,
        "open_time": 1234567800,
        "resolution_time": 1234568100,  # 5 minutes later
        "up_token": "token_up_123",
        "down_token": "token_down_123",
        "price": 0.50,
        "best_ask": {"up": 0.50, "down": 0.50},
        "elapsed_seconds": 0,
    }


@pytest.fixture
def mock_prices_up():
    """Mock price data showing UP signal."""
    return {
        "binance": 105100,
        "coinbase": 105120,
        "chainlink": 105000,
    }


@pytest.fixture
def mock_prices_down():
    """Mock price data showing DOWN signal."""
    return {
        "binance": 104900,
        "coinbase": 104880,
        "chainlink": 105000,
    }


@pytest.fixture
def mock_orderbook_bullish():
    """Mock order book showing bullish imbalance."""
    return {
        "bids": [{"price": 0.55, "size": 2000}] * 10,  # 2.0 ratio > 1.8 threshold
        "asks": [{"price": 0.56, "size": 1000}] * 10,
    }


@pytest.fixture
def mock_orderbook_bearish():
    """Mock order book showing bearish imbalance."""
    return {
        "bids": [{"price": 0.44, "size": 500}] * 10,
        "asks": [{"price": 0.45, "size": 1000}] * 10,
    }


@pytest.fixture
def mock_orderbook_neutral():
    """Mock order book showing neutral (no signal)."""
    return {
        "bids": [{"price": 0.50, "size": 500}] * 10,
        "asks": [{"price": 0.51, "size": 500}] * 10,
    }


@pytest.fixture
def mock_position():
    """Mock open position."""
    return {
        "token_id": "token_up_123",
        "direction": "UP",
        "entry_price": 0.50,
        "size": 100,
        "order_id": "test_order_123",
        "market": {
            "resolution_time": 1234568100,
        },
    }
