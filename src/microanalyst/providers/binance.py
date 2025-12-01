import time
import requests
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BinanceClient:
    """
    Client for Binance Public API.
    Handles rate limiting (weight-based) and data fetching.
    """
    BASE_URL = "https://api.binance.us/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        # Binance limits are 1200 weight per minute.
        # We will implement a simple backoff if 429 is hit, 
        # and generally try not to spam.
    
    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Internal request method with error handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.warning(f"Binance rate limit hit. Waiting {retry_after}s...")
                time.sleep(retry_after)
                return self._request(endpoint, params)
            elif e.response.status_code == 418: # IP ban
                logger.critical("Binance IP Ban! Stop immediately.")
                raise e
            logger.error(f"HTTP Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def get_ticker_24h(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches 24hr rolling window price change statistics.
        Endpoint: /api/v3/ticker/24hr
        Weight: 1
        """
        params = {"symbol": symbol.upper()}
        return self._request("ticker/24hr", params=params)

    def get_depth(self, symbol: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Fetches order book depth.
        Endpoint: /api/v3/depth
        Weight: Adjusted based on limit (1-100: 1, 101-500: 5, etc.)
        """
        params = {
            "symbol": symbol.upper(),
            "limit": limit
        }
        return self._request("depth", params=params)

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 500) -> Optional[List[Any]]:
        """
        Fetches candlestick data.
        Endpoint: /api/v3/klines
        Weight: 1
        """
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        return self._request("klines", params=params)

    def get_agg_trades(self, symbol: str, limit: int = 500) -> Optional[List[Any]]:
        """
        Fetches compressed, aggregate trades.
        Endpoint: /api/v3/aggTrades
        Weight: 1
        """
        params = {
            "symbol": symbol.upper(),
            "limit": limit
        }
        return self._request("aggTrades", params=params)
