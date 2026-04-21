"""Tests for signals module - signal combination logic."""



def test_should_trade_both_signals_up(mock_prices_up, mock_orderbook_bullish, mock_market):
    """Test UP signal when both price divergence and order book agree."""
    from src.signals import should_trade

    signal = should_trade(mock_prices_up, mock_orderbook_bullish, mock_market)

    assert signal is not None
    assert signal["direction"] == "UP"
    assert 0 < signal["confidence"] <= 0.95
    assert signal["size"] > 0
    assert signal["imbalance"] == 2.0  # Updated to match fixture


def test_should_trade_both_signals_down(mock_prices_down, mock_orderbook_bearish, mock_market):
    """Test DOWN signal when both price divergence and order book agree."""
    from src.signals import should_trade

    signal = should_trade(mock_prices_down, mock_orderbook_bearish, mock_market)

    assert signal is not None
    assert signal["direction"] == "DOWN"
    assert 0 < signal["confidence"] <= 0.95
    assert signal["imbalance"] == 0.5


def test_should_trade_no_signal_exchanges_disagree(mock_orderbook_bullish, mock_market):
    """Test no signal when Binance and Coinbase disagree."""
    from src.signals import should_trade

    # Binance above, Coinbase below
    prices = {"binance": 105100, "coinbase": 104900, "chainlink": 105000}

    signal = should_trade(prices, mock_orderbook_bullish, mock_market)
    assert signal is None


def test_should_trade_no_signal_small_divergence(mock_orderbook_bullish, mock_market):
    """Test no signal when divergence is below $50 threshold."""
    from src.signals import should_trade

    # Only $40 divergence - below $50 threshold
    prices = {"binance": 105040, "coinbase": 105035, "chainlink": 105000}

    signal = should_trade(prices, mock_orderbook_bullish, mock_market)
    assert signal is None


def test_should_trade_no_signal_book_neutral(mock_prices_up, mock_orderbook_neutral, mock_market):
    """Test no signal when order book doesn't confirm price divergence."""
    from src.signals import should_trade

    signal = should_trade(mock_prices_up, mock_orderbook_neutral, mock_market)
    assert signal is None


def test_should_trade_no_signal_wrong_book_direction(mock_prices_up, mock_orderbook_bearish, mock_market):
    """Test no signal when order book contradicts price divergence."""
    from src.signals import should_trade

    # Price says UP, but book is bearish
    signal = should_trade(mock_prices_up, mock_orderbook_bearish, mock_market)
    assert signal is None


def test_confidence_increases_with_stronger_signals(mock_orderbook_bullish, mock_market):
    """Test that confidence increases with stronger divergence."""
    from src.signals import should_trade

    # Weak divergence
    weak_prices = {"binance": 105060, "coinbase": 105055, "chainlink": 105000}
    weak_signal = should_trade(weak_prices, mock_orderbook_bullish, mock_market)

    # Strong divergence
    strong_prices = {"binance": 105300, "coinbase": 105280, "chainlink": 105000}
    strong_signal = should_trade(strong_prices, mock_orderbook_bullish, mock_market)

    assert weak_signal is not None
    assert strong_signal is not None
    assert strong_signal["confidence"] > weak_signal["confidence"]


def test_confidence_capped_at_95_percent(mock_orderbook_bullish, mock_market):
    """Test that confidence is capped at 0.95."""
    from src.signals import should_trade

    # Extreme divergence that would exceed 0.95
    extreme_prices = {"binance": 110000, "coinbase": 110000, "chainlink": 105000}

    signal = should_trade(extreme_prices, mock_orderbook_bullish, mock_market)
    assert signal is not None
    assert signal["confidence"] <= 0.95
