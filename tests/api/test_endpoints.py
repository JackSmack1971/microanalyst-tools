import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.server import app
from src.microanalyst.services.analyzer import TokenAnalyzer

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("src.api.server.analyzer")
def test_analyze_token_success(mock_analyzer):
    # Mock analyzer response
    mock_data = {
        "token_symbol": "eth",
        "volatility": 0.05,
        "prices": [100, 101]
    }
    mock_analyzer.analyze.return_value = mock_data
    
    response = client.get("/api/analyze/eth?days=30")
    
    assert response.status_code == 200
    assert response.json() == mock_data
    mock_analyzer.analyze.assert_called_with("eth", 30, btc_volatility=None)

@patch("src.api.server.analyzer")
def test_analyze_token_not_found(mock_analyzer):
    mock_analyzer.analyze.return_value = None
    
    response = client.get("/api/analyze/invalid")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@patch("src.api.server.analyzer")
def test_analyze_token_server_error(mock_analyzer):
    mock_analyzer.analyze.side_effect = Exception("API Error")
    
    response = client.get("/api/analyze/error")
    
    assert response.status_code == 500
    assert "API Error" in response.json()["detail"]
