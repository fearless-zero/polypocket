"""Tests for prices module - multi-source price fetching."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_prices_success():
    """Test successful price fetching from all sources."""
    from src.prices import get_prices

    async def mock_binance_get(*args, **kwargs):
        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value={"price": "105100.50"})
        return mock_resp

    async def mock_coinbase_get(*args, **kwargs):
        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value={"data": {"amount": "105120.75"}})
        return mock_resp

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock(side_effect=[
            mock_binance_get(),
            mock_coinbase_get(),
        ])
        mock_session.return_value = mock_session_instance

        with patch("src.prices.get_chainlink_price", return_value=105000.0):
            prices = await get_prices()

            assert prices["binance"] == 105100.50
            assert prices["coinbase"] == 105120.75
            assert prices["chainlink"] == 105000.0


def test_get_chainlink_price():
    """Test Chainlink price fetching."""
    from src.prices import get_chainlink_price

    mock_contract = MagicMock()
    mock_contract.functions.latestRoundData.return_value.call.return_value = (
        1, 10500000000000, 1234567890, 1234567890, 1  # answer with 8 decimals
    )

    with patch("src.prices.Web3") as mock_web3_class:
        mock_web3_instance = MagicMock()
        mock_web3_instance.eth.contract.return_value = mock_contract
        mock_web3_class.return_value = mock_web3_instance
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        price = get_chainlink_price()
        assert price == 105000.0
