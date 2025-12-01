from datetime import datetime
from typing import Dict, Any

def generate_report(
    token_symbol: str,
    cg_data: Dict[str, Any],
    binance_ticker: Dict[str, Any],
    volatility_metrics: Dict[str, float],
    volume_metrics: Dict[str, float],
    liquidity_metrics: Dict[str, float],
    validation_flags: Dict[str, Any]
) -> str:
    """
    Generates the Standard Analysis Report in Markdown format.
    """
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Extract Data
    market_cap = cg_data.get("market_data", {}).get("market_cap", {}).get("usd", "N/A")
    rank = cg_data.get("market_cap_rank", "N/A")
    
    # Format Metrics
    cv = f"{volatility_metrics.get('cv', 0.0):.2f}"
    bb_width = f"{volatility_metrics.get('bb_width', 0.0):.1f}%"
    ath_dist = f"{cg_data.get('market_data', {}).get('ath_change_percentage', {}).get('usd', 0.0):.1f}%"
    
    spread = f"{liquidity_metrics.get('spread_pct', 0.0):.2f}%"
    depth_2pct = f"${liquidity_metrics.get('depth_2pct', 0.0):,.0f}"
    imbalance = f"{liquidity_metrics.get('imbalance', 0.0):.2f}"
    
    vol_change = f"{volume_metrics.get('vol_change_7d', 0.0):+.1f}%"
    
    # Validation Section
    cg_vol = cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 0)
    bin_vol = float(binance_ticker.get("quoteVolume", 0))
    vol_delta = ((abs(cg_vol - bin_vol)) / cg_vol * 100) if cg_vol else 0.0
    
    
    report = f"""## TOKEN OVERVIEW
Symbol: {token_symbol.upper()} | Rank: #{rank} | Market Cap: ${market_cap:,.0f}
Data Sources: CoinGecko (last updated: {cg_data.get('last_updated', 'N/A')}) + Binance (live)

## QUANTITATIVE METRICS
1. Volatility Assessment
   - 30D Coefficient of Variation: {cv}
   - Bollinger Band Width (20D): {bb_width}
   - ATH Distance: {ath_dist}

2. Liquidity Profile
   - Bid-Ask Spread (Binance): {spread}
   - ±2% Order Book Depth: {depth_2pct}
   - Order Book Imbalance: {imbalance} (>1 = bid pressure)

3. Volume Intelligence
   - 24h Volume vs 7D Average: {vol_change}
   - CoinGecko-Binance Volume Delta: {vol_delta:.1f}%
   
## PATTERN RECOGNITION
- Historical pattern analysis requires manual interpretation of the charts.
- Current metrics suggest {'HIGH' if float(cv) > 0.1 else 'LOW'} volatility environment.

## RISK FACTORS
"""
    
    # Add Risk Factors
    if float(spread.strip('%')) > 0.5:
        report += f"- [WARNING] Wide Bid-Ask Spread: {spread}\n"
    if vol_delta > 20:
        report += f"- [WARNING] Significant Volume Discrepancy: {vol_delta:.1f}%\n"
    if float(imbalance) < 0.5 or float(imbalance) > 2.0:
        report += f"- [NOTE] High Order Book Imbalance: {imbalance}\n"
        
    report += f"""
## REFERENCE DATA
- Analysis Timestamp: {timestamp}
- API Call Count: Optimized (Batched/Cached)
- Data Confidence: {'Low' if vol_delta > 50 else 'High'}
"""
    return report
