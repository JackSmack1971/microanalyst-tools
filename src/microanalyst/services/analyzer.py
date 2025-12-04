import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.microanalyst.providers.coingecko import CoinGeckoClient
from src.microanalyst.providers.binance import BinanceClient
from src.microanalyst.analysis.metrics import (
    calculate_volatility_metrics,
    calculate_volume_metrics,
    calculate_liquidity_metrics,
    calculate_technical_indicators
)

logger = logging.getLogger("microanalyst")

class TokenAnalyzer:
    def __init__(self, cg_client: CoinGeckoClient, binance_client: BinanceClient):
        self.cg_client = cg_client
        self.binance_client = binance_client

    def analyze(self, token_symbol: str, days: int, btc_volatility: Optional[float] = None, callback: Optional[Callable[[str, Optional[str]], None]] = None) -> Optional[Dict[str, Any]]:
        """
        Analyzes a single token and returns all relevant data and metrics.
        
        Args:
            token_symbol: The symbol or name of the token to analyze.
            days: Number of days of historical data to fetch.
            btc_volatility: Optional BTC volatility for beta calculation.
            callback: Optional callback function(step, description) for progress updates.
                      Steps: "search", "market", "orderbook", "analysis".
        """
        # Search
        if callback:
            callback("search", f"Searching {token_symbol}...")
            
        try:
            search_results = self.cg_client.search(token_symbol)
        except Exception as e:
            logger.error(f"Search failed for {token_symbol}: {e}")
            return None
        
        if not search_results or not search_results.get("coins"):
            logger.error(f"Token {token_symbol} not found.")
            return None
        
        # Default behavior: pick first
        token_id = search_results["coins"][0]["id"]
        token_symbol_api = search_results["coins"][0]["symbol"]
        
        if callback:
            callback("search", None) # Advance search
            callback("market", f"Fetching data for {token_symbol_api}...")

        # Fetch Market Data
        try:
            cg_data = self.cg_client.get_token_data(token_id)
            market_chart = self.cg_client.get_market_chart(token_id, days=days)
            
            # Check for cache hit
            is_cached = cg_data.get("_from_cache", False) or market_chart.get("_from_cache", False)
            
            # Clean up cache flags
            if cg_data: cg_data.pop("_from_cache", None)
            if market_chart: market_chart.pop("_from_cache", None)
                
        except Exception as e:
            logger.error(f"Data fetch failed for {token_id}: {e}")
            return None
        
        if not cg_data or not market_chart:
            return None
            
        if callback:
            callback("market", None) # Advance market
            desc = f"Fetching orderbook for {token_symbol_api}..."
            if is_cached:
                desc += " [green](Cached)[/green]"
            callback("orderbook", desc)

        # Binance Data
        binance_symbol = f"{token_symbol_api.upper()}USDT"
        ticker_24h = self.binance_client.get_ticker_24h(binance_symbol)
        depth = self.binance_client.get_depth(binance_symbol)
        
        if not ticker_24h:
            ticker_24h = {}
            depth = {"bids": [], "asks": []}
            
        if callback:
            callback("orderbook", None) # Advance orderbook
            callback("analysis", f"Analyzing {token_symbol_api}...")

        # Analyze
        prices_data = market_chart.get("prices", [])
        volumes_data = market_chart.get("total_volumes", [])
        
        prices = [p[1] for p in prices_data]
        volumes = [v[1] for v in volumes_data]
        
        # Extract dates for charts (convert ms timestamp to datetime string)
        dates = [datetime.fromtimestamp(p[0]/1000).strftime("%Y-%m-%d") for p in prices_data]
        
        volatility_metrics = calculate_volatility_metrics(prices)
        volume_metrics = calculate_volume_metrics(prices, volumes)
        liquidity_metrics = calculate_liquidity_metrics(depth)
        ta_metrics = calculate_technical_indicators(prices)
        
        # Calculate derived values
        cg_vol = cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 0)
        bin_vol = float(ticker_24h.get("quoteVolume", 0))
        vol_delta = ((abs(cg_vol - bin_vol)) / cg_vol * 100) if cg_vol else 0.0
    
        beta_proxy = None
        if btc_volatility and volatility_metrics.get("cv"):
            beta_proxy = volatility_metrics["cv"] / btc_volatility
        
        if callback:
            callback("analysis", None) # Advance analysis
    
        return {
            "token_symbol": token_symbol,
            "token_symbol_api": token_symbol_api,
            "cg_data": cg_data,
            "ticker_24h": ticker_24h,
            "volatility_metrics": volatility_metrics,
            "volume_metrics": volume_metrics,
            "liquidity_metrics": liquidity_metrics,
            "ta_metrics": ta_metrics,
            "vol_delta": vol_delta,
            "beta_proxy": beta_proxy,
            # Flattened metrics for comparison
            "volatility": volatility_metrics.get("cv"),
            "spread": liquidity_metrics.get("spread_pct"),
            "volume_delta": vol_delta,
            "imbalance": liquidity_metrics.get("imbalance"),
            # Chart data
            "dates": dates,
            "prices": prices,
            "volumes": volumes
        }
