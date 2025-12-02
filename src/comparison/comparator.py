import pandas as pd
from typing import List, Dict, Any, Tuple
from src.visualization.sparkline import generate_sparkline

def compare_tokens(results: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compares multiple token analysis results.
    
    Args:
        results: List of analysis result dictionaries.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: 
            - Metrics DataFrame (comparison table)
            - Correlation Matrix DataFrame
    """
    if not results:
        return pd.DataFrame(), pd.DataFrame()
        
    # 1. Build Metrics DataFrame
    rows = []
    for res in results:
        # Handle potential missing keys gracefully
        volatility = res.get("volatility", {}) or {}
        liquidity = res.get("liquidity", {}) or {}
        
        # Support both flat structure (from main.py flattened) and nested
        cv = volatility.get("cv") if isinstance(volatility, dict) else res.get("volatility")
        spread = liquidity.get("spread_pct") if isinstance(liquidity, dict) else res.get("spread")
        depth = liquidity.get("depth_2pct") if isinstance(liquidity, dict) else res.get("depth_2pct")
        
        # Extract prices for sparkline
        prices = [p[1] for p in res.get("prices", [])]
        sparkline = generate_sparkline(prices)
        
        row = {
            "Symbol": res.get("symbol", "UNKNOWN").upper(),
            "Price": res.get("current_price", 0),
            "7d Trend": sparkline,
            "Market Cap": res.get("market_cap", 0),
            "Volume": res.get("total_volume", 0),
            "CV (Vol)": cv,
            "Spread %": spread,
            "Depth ±2%": depth
        }
        rows.append(row)
    
    metrics_df = pd.DataFrame(rows)
    
    # 2. Build Correlation Matrix
    # Extract price series for each token
    price_data = {}
    for res in results:
        # res["prices"] is a list of [timestamp, price]
        # Convert to Series with timestamp index
        if "prices" in res and res["prices"]:
            df = pd.DataFrame(res["prices"], columns=["timestamp", "price"])
            # Ensure timestamp is numeric
            df["timestamp"] = pd.to_numeric(df["timestamp"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
            df.set_index("timestamp", inplace=True)
            
            # Resample to daily to align data points (handling different timestamps)
            # Using 'D' (Daily) mean price
            daily_prices = df["price"].resample('D').mean()
            price_data[res.get("symbol", "UNKNOWN").upper()] = daily_prices
            
    if price_data:
        price_df = pd.DataFrame(price_data)
        # Drop rows with missing data to ensure fair correlation
        price_df.dropna(inplace=True)
        if not price_df.empty:
            correlation_df = price_df.corr(method='pearson')
        else:
            correlation_df = pd.DataFrame()
    else:
        correlation_df = pd.DataFrame()
        
    return metrics_df, correlation_df
