import time
import requests
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class CoinGeckoClient:
    """
    Client for CoinGecko API (Free Tier).
    Handles rate limiting and data fetching for token analysis.
    """
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.request_interval = 6.0  # Conservative 10 calls/minute for free tier to be safe
        # Free tier is actually ~10-30 calls/min, but we want to avoid 429s aggressively.

    def _wait_for_rate_limit(self):
        """Ensures we respect the rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Internal request method with error handling and rate limiting."""
        self._wait_for_rate_limit()
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("CoinGecko rate limit hit. Waiting 60s...")
                time.sleep(60)
                return self._request(endpoint, params) # Retry once
            logger.error(f"HTTP Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def get_token_data(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches detailed token data including market cap, supply, and ATH.
        Endpoint: /coins/{id}
        """
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        return self._request(f"coins/{token_id}", params=params)

    def get_market_chart(self, token_id: str, days: str = "30") -> Optional[Dict[str, Any]]:
        """
        Fetches historical OHLCV data.
        Endpoint: /coins/{id}/market_chart
        """
        params = {
            "vs_currency": "usd",
            "days": days
        }
        return self._request(f"coins/{token_id}/market_chart", params=params)

    def get_simple_price(self, ids: List[str], vs_currencies: str = "usd") -> Optional[Dict[str, Any]]:
        """
        Fetches simple price data.
        Endpoint: /simple/price
        """
        params = {
            "ids": ",".join(ids),
            "vs_currencies": vs_currencies,
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        return self._request("simple/price", params=params)
