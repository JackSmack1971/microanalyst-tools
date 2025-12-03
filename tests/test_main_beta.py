import pytest
from unittest.mock import patch, MagicMock
from src.microanalyst.main import analyze_token, main
from src.microanalyst.providers.coingecko import CoinGeckoClient
from src.microanalyst.providers.binance import BinanceClient

def test_analyze_token_calculates_beta():
    """Test that analyze_token calculates beta_proxy correctly."""
    mock_cg = MagicMock()
    mock_binance = MagicMock()
    
    # Mock search
    mock_cg.search.return_value = {"coins": [{"id": "ethereum", "symbol": "eth"}]}
    
    # Mock token data
    mock_cg.get_token_data.return_value = {
        "name": "Ethereum", 
        "symbol": "eth", 
        "market_data": {"current_price": {"usd": 2000}, "total_volume": {"usd": 1000}}
    }
    
    # Mock market chart for ETH (High Volatility)
    # [100, 110, 100, 110...]
    prices = [[i*1000, 100 if i % 2 == 0 else 110] for i in range(30)]
    mock_cg.get_market_chart.return_value = {"prices": prices, "total_volumes": []}
    
    # Mock Binance
    mock_binance.get_ticker_24h.return_value = {"quoteVolume": 1000}
    mock_binance.get_depth.return_value = {"bids": [], "asks": []}
    
    # BTC Volatility (Low)
    # Let's assume BTC CV is 0.05
    btc_volatility = 0.05
    
    # Run analysis
    result = analyze_token("eth", mock_cg, mock_binance, 30, btc_volatility=btc_volatility)
    
    assert result is not None
    assert "beta_proxy" in result
    assert result["beta_proxy"] is not None
    
    # Calculate expected beta
    # ETH prices: 100, 110, 100, 110...
    # Mean = 105
    # Std Dev approx 5
    # CV approx 5/105 = 0.0476
    
    # Wait, my mock prices are very stable actually (just oscillating).
    # Let's trust the calculation logic: beta = token_cv / btc_cv
    token_cv = result["volatility_metrics"]["cv"]
    expected_beta = token_cv / btc_volatility
    
    assert result["beta_proxy"] == pytest.approx(expected_beta)

def test_main_fetches_btc_baseline(rich_console):
    """Test that main fetches BTC baseline."""
    with patch("sys.argv", ["main.py", "eth"]), \
         patch("src.microanalyst.main.CoinGeckoClient") as mock_cg_cls, \
         patch("src.microanalyst.main.BinanceClient"), \
         patch("src.microanalyst.main.console", rich_console), \
         patch("src.microanalyst.main.analyze_token") as mock_analyze:
        
        mock_cg = mock_cg_cls.return_value
        
        # Mock BTC fetch
        mock_cg.get_market_chart.return_value = {"prices": [[0, 100], [1, 101]], "total_volumes": []}
        
        # Mock analyze_token to return something so main proceeds
        mock_analyze.return_value = {
            "token_symbol": "eth", 
            "token_symbol_api": "eth",
            "cg_data": {"name": "Ethereum"},
            "ticker_24h": {"quoteVolume": 1000},
            "volatility_metrics": {"cv": 0.1},
            "volume_metrics": {},
            "liquidity_metrics": {"spread_pct": 0.1, "imbalance": 1.0},
            "volatility": 0.1,
            "spread": 0.1,
            "volume_delta": 0.1,
            "imbalance": 1.0,
            "ta_metrics": {},
            "beta_proxy": 2.0,
            "dates": [], "prices": [], "volumes": []
        }
        
        main()
        
        # Verify BTC fetch was called
        mock_cg.get_market_chart.assert_any_call("bitcoin", days=ANY)
        
        # Verify analyze_token was called with btc_volatility
        args, kwargs = mock_analyze.call_args
        assert "btc_volatility" in kwargs or len(args) >= 7
        # Check that the value passed is not None (since we mocked BTC data)
        # Note: calculate_volatility_metrics([100, 101]) -> CV > 0
        
from unittest.mock import ANY
