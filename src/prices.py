"""
Step 1: Multi-Source Price Divergence
Pull BTC prices from Binance, Coinbase, and Chainlink in parallel.
"""

import asyncio
import aiohttp
from web3 import Web3
from .config import CHAINLINK_RPC, CHAINLINK_AGGREGATOR_ADDRESS


# Chainlink ABI (minimal - just latestRoundData)
CHAINLINK_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def get_chainlink_price() -> float:
    """Read BTC/USD price from Chainlink on-chain feed."""
    w3 = Web3(Web3.HTTPProvider(CHAINLINK_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CHAINLINK_AGGREGATOR_ADDRESS),
        abi=CHAINLINK_ABI,
    )
    _, answer, _, updated_at, _ = contract.functions.latestRoundData().call()
    # Chainlink BTC/USD has 8 decimals
    return answer / 1e8


async def get_prices() -> dict:
    """
    Fetch BTC price from three sources in parallel:
    - Binance REST API
    - Coinbase REST API
    - Chainlink on-chain feed (via web3)
    """
    async with aiohttp.ClientSession() as session:
        binance_req = session.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        coinbase_req = session.get("https://api.coinbase.com/v2/prices/BTC-USD/spot")
        # Chainlink is synchronous (web3 call), run in executor
        loop = asyncio.get_event_loop()
        chainlink_fut = loop.run_in_executor(None, get_chainlink_price)

        results = await asyncio.gather(binance_req, coinbase_req, chainlink_fut)

    binance_price = float((await results[0].json())["price"])
    coinbase_price = float((await results[1].json())["data"]["amount"])
    chainlink_price = results[2]

    return {
        "binance": binance_price,
        "coinbase": coinbase_price,
        "chainlink": chainlink_price,
    }
