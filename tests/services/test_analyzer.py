import pytest
from unittest.mock import MagicMock, ANY
from src.microanalyst.services.analyzer import TokenAnalyzer
from src.microanalyst.providers.coingecko import CoinGeckoClient
from src.microanalyst.providers.binance import BinanceClient

def test_analyzer_analyze_flow():
    """Test the analyze method flow."""
    mock_cg = MagicMock()
    mock_binance = MagicMock()
    
    analyzer = TokenAnalyzer(mock_cg, mock_binance)
    
    # Mock search
    mock_cg.search.return_value = {"coins": [{"id": "ethereum", "symbol": "eth"}]}
    
    # Mock token data
    mock_cg.get_token_data.return_value = {
        "name": "Ethereum", 
        "symbol": "eth", 
        "market_data": {"current_price": {"usd": 2000}, "total_volume": {"usd": 1000}}
    }
    
    # Mock market chart
    prices = [[i*1000, 100] for i in range(30)]
    mock_cg.get_market_chart.return_value = {"prices": prices, "total_volumes": []}
    
    # Mock Binance
    mock_binance.get_ticker_24h.return_value = {"quoteVolume": 1000}
    mock_binance.get_depth.return_value = {"bids": [], "asks": []}
    
    # Callback mock
    mock_callback = MagicMock()
    
    result = analyzer.analyze("eth", 30, callback=mock_callback)
    
    assert result is not None
    assert result["token_symbol"] == "eth"
    assert result["token_symbol_api"] == "eth"
    assert "risk_metrics" in result
    assert "advanced_ta" in result
    assert "macd" in result["advanced_ta"]
    assert "fibonacci" in result["advanced_ta"]
    
    # Verify callback calls
    # Should be called for search, market, orderbook, analysis
    assert mock_callback.call_count >= 4
    mock_callback.assert_any_call("search", ANY)
    mock_callback.assert_any_call("market", ANY)
    
def test_analyzer_returns_none_on_search_fail():
    """Test analyzer returns None if search fails."""
    mock_cg = MagicMock()
    mock_binance = MagicMock()
    analyzer = TokenAnalyzer(mock_cg, mock_binance)
    
    mock_cg.search.return_value = {}
    
    result = analyzer.analyze("invalid", 30)
    assert result is None
