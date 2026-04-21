"""
Configuration — load from environment variables.
Copy .env.example to .env and fill in your values.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Polymarket CLOB API credentials
# Get from: https://clob.polymarket.com
POLYMARKET_API_KEY = os.getenv("POLYMARKET_API_KEY", "")
POLYMARKET_API_SECRET = os.getenv("POLYMARKET_API_SECRET", "")
POLYMARKET_API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE", "")

# Chainlink on-chain price feed (Polygon mainnet)
CHAINLINK_RPC = os.getenv("CHAINLINK_RPC", "https://polygon-rpc.com")
# BTC/USD Chainlink aggregator on Polygon
CHAINLINK_AGGREGATOR_ADDRESS = os.getenv(
    "CHAINLINK_AGGREGATOR_ADDRESS", "0xc907E116054Ad103354f2D350FD2514433D57F6f"
)

# Trading parameters
BANKROLL = float(os.getenv("BANKROLL", "2000"))
PROFIT_TARGET = float(os.getenv("PROFIT_TARGET", "0.75"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "0.35"))
ENTRY_WINDOW_MIN = int(os.getenv("ENTRY_WINDOW_MIN", "60"))  # seconds after open
ENTRY_WINDOW_MAX = int(os.getenv("ENTRY_WINDOW_MAX", "180"))  # seconds after open

# Signal thresholds
PRICE_DIVERGENCE_THRESHOLD = float(os.getenv("PRICE_DIVERGENCE_THRESHOLD", "50"))  # USD
ORDER_BOOK_IMBALANCE_UP = float(os.getenv("ORDER_BOOK_IMBALANCE_UP", "1.8"))
ORDER_BOOK_IMBALANCE_DOWN = float(os.getenv("ORDER_BOOK_IMBALANCE_DOWN", "0.55"))
