import time
import requests
import logging
from typing import Dict, Any, Optional, List
from src.cache.manager import get_cache

logger = logging.getLogger(__name__)

class CoinGeckoClient:
    """
    Client for CoinGecko API (Free Tier).
    Handles rate limiting and data fetching for token analysis.
    """
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, status_callback=None):
        self.session = requests.Session()
        self.last_request_time = 0
        self.request_interval = 6.0  # Conservative 10 calls/minute for free tier to be safe
        # Free tier is actually ~10-30 calls/min, but we want to avoid 429s aggressively.
        self.status_callback = status_callback

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
                msg = "CoinGecko rate limit hit. Waiting 60s..."
                logger.warning(msg)
                if self.status_callback:
                    self.status_callback(msg)
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
        # Check Cache
        cache = get_cache()
        cache_key = f"coingecko:token:{token_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            cached_data["_from_cache"] = True
            return cached_data

        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        data = self._request(f"coins/{token_id}", params=params)
        
        if data:
            # Cache for 5 minutes
            cache.set(cache_key, data, expire=300)
            data["_from_cache"] = False
            
        return data

    def get_market_chart(self, token_id: str, days: str = "30") -> Optional[Dict[str, Any]]:
        """
        Fetches historical OHLCV data.
        Endpoint: /coins/{id}/market_chart
        """
        # Check Cache
        cache = get_cache()
        cache_key = f"coingecko:chart:{token_id}:{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            cached_data["_from_cache"] = True
            return cached_data

        params = {
            "vs_currency": "usd",
            "days": days
        }
        data = self._request(f"coins/{token_id}/market_chart", params=params)
        
        if data:
            # Cache for 5 minutes
            cache.set(cache_key, data, expire=300)
            data["_from_cache"] = False
            
        return data

    def get_simple_price(self, ids: List[str], vs_currencies: str = "usd") -> Optional[Dict[str, Any]]:
        """
        Fetches simple price data.
        Endpoint: /simple/price
        """
        # Simple price is often real-time critical, maybe shorter cache or no cache?
        # Let's cache for 1 minute to avoid spamming during rapid testing
        cache = get_cache()
        ids_str = ",".join(sorted(ids))
        cache_key = f"coingecko:price:{ids_str}:{vs_currencies}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        params = {
            "ids": ",".join(ids),
            "vs_currencies": vs_currencies,
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        data = self._request("simple/price", params=params)
        
        if data:
            cache.set(cache_key, data, expire=60)
            
        return data
