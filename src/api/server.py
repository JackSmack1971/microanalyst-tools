from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from src.microanalyst.providers.coingecko import CoinGeckoClient
from src.microanalyst.providers.binance import BinanceClient
from src.microanalyst.services.analyzer import TokenAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("microanalyst-api")

app = FastAPI(
    title="Microanalyst API",
    description="API for Cryptocurrency Microanalyst Tools",
    version="0.1.0"
)

# Initialize Clients
# In a real production app, we might use dependency injection or lifespan events
cg_client = CoinGeckoClient()
binance_client = BinanceClient()
analyzer = TokenAnalyzer(cg_client, binance_client)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/analyze/{token}")
async def analyze_token(
    token: str, 
    days: int = Query(30, description="Number of days of historical data"),
    btc_volatility: Optional[float] = Query(None, description="Optional BTC volatility for beta calculation")
) -> Dict[str, Any]:
    """
    Analyze a token and return metrics.
    """
    try:
        logger.info(f"Analyzing token: {token} (days={days})")
        result = analyzer.analyze(token, days, btc_volatility=btc_volatility)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Token '{token}' not found or analysis failed")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
