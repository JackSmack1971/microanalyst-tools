"""
Cache Manager for Microanalyst Tools.
Provides a persistent file-based cache using diskcache.
"""
import os
from pathlib import Path
from diskcache import Cache

# Default cache location: ~/.microanalyst/cache
CACHE_DIR = Path.home() / ".microanalyst" / "cache"

class CacheManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Ensure directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        # Initialize diskcache
        # size_limit: 100MB (should be plenty for JSON data)
        self.cache = Cache(str(CACHE_DIR), size_limit=100 * 1024 * 1024)
        
    def get(self, key):
        return self.cache.get(key)
        
    def set(self, key, value, expire=None):
        """
        Set value in cache.
        expire: Seconds until expiration (default None = forever)
        """
        self.cache.set(key, value, expire=expire)
        
    def clear(self):
        self.cache.clear()
        
    def close(self):
        self.cache.close()

# Global instance accessor
_cache_manager = None

def get_cache() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
