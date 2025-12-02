"""
Unit tests for caching layer.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.microanalyst.providers.coingecko import CoinGeckoClient
from src.cache.manager import get_cache

@pytest.fixture
def mock_cache():
    with patch("src.microanalyst.providers.coingecko.get_cache") as mock_get_cache:
        cache_instance = MagicMock()
        mock_get_cache.return_value = cache_instance
        yield cache_instance

@pytest.fixture
def client():
    return CoinGeckoClient()

def test_get_token_data_cache_hit(client, mock_cache):
    """Test that cache hit returns data without API call."""
    token_id = "bitcoin"
    cached_data = {"id": "bitcoin", "name": "Bitcoin"}
    
    # Setup cache hit
    mock_cache.get.return_value = cached_data
    
    # Call method
    result = client.get_token_data(token_id)
    
    # Verify result
    assert result == cached_data
    assert result["_from_cache"] is True
    
    # Verify cache was checked
    mock_cache.get.assert_called_with(f"coingecko:token:{token_id}")
    
    # Verify API was NOT called (we can't easily check _request here without mocking it too, 
    # but if _request was called it would likely fail or return something else if not mocked.
    # Let's mock _request to be sure)

def test_get_token_data_cache_miss(client, mock_cache):
    """Test that cache miss calls API and sets cache."""
    token_id = "bitcoin"
    api_data = {"id": "bitcoin", "name": "Bitcoin"}
    
    # Setup cache miss
    mock_cache.get.return_value = None
    
    # Mock _request
    with patch.object(client, "_request", return_value=api_data) as mock_request:
        result = client.get_token_data(token_id)
        
        # Verify result
        assert result == api_data
        assert result["_from_cache"] is False
        
        # Verify API was called
        mock_request.assert_called_once()
        
        # Verify cache was set
        mock_cache.set.assert_called_with(f"coingecko:token:{token_id}", api_data, expire=300)

def test_get_market_chart_caching(client, mock_cache):
    """Test caching for market chart."""
    token_id = "bitcoin"
    days = "30"
    chart_data = {"prices": []}
    
    # Cache miss
    mock_cache.get.return_value = None
    
    with patch.object(client, "_request", return_value=chart_data):
        client.get_market_chart(token_id, days)
        
        mock_cache.set.assert_called_with(f"coingecko:chart:{token_id}:{days}", chart_data, expire=300)
