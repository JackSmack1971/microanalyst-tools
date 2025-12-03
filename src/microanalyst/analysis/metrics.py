import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

def calculate_volatility_metrics(prices: List[float]) -> Dict[str, float]:
    """
    Calculates volatility metrics:
    - Coefficient of Variation (CV)
    - Bollinger Band Width (20D)
    """
    if not prices or len(prices) < 20:
        return {"cv": 0.0, "bb_width": 0.0, "ath_distance": 0.0}
    
    series = pd.Series(prices)
    
    # Coefficient of Variation
    mean = series.mean()
    std_dev = series.std()
    cv = std_dev / mean if mean != 0 else 0.0
    
    # Bollinger Bands (20 periods)
    sma_20 = series.rolling(window=20).mean().iloc[-1]
    std_20 = series.rolling(window=20).std().iloc[-1]
    upper_band = sma_20 + (2 * std_20)
    lower_band = sma_20 - (2 * std_20)
    
    bb_width = ((upper_band - lower_band) / sma_20) * 100 if sma_20 != 0 else 0.0
    
    return {
        "cv": cv,
        "bb_width": bb_width,
        "ath_distance": 0.0 # Placeholder, calculated separately with ATH data
    }

def calculate_volume_metrics(prices: List[float], volumes: List[float]) -> Dict[str, float]:
    """
    Calculates volume intelligence metrics:
    - VWAP Deviation (Simplified for available data)
    - Volume Rate of Change (VROC) - implied by volume delta in report
    """
    # Note: True VWAP requires intraday tick data, but we can approximate or use 
    # the relationship between volume and price trends.
    # For this tool, we will focus on the explicit metrics requested in the prompt
    # which are mostly derived from comparing current volume to averages.
    
    if not volumes:
        return {"vol_change_7d": 0.0}

    current_vol = volumes[-1]
    avg_vol_7d = np.mean(volumes[-7:]) if len(volumes) >= 7 else np.mean(volumes)
    
    vol_change = ((current_vol - avg_vol_7d) / avg_vol_7d) * 100 if avg_vol_7d != 0 else 0.0
    
    return {
        "vol_change_7d": vol_change
    }

def calculate_liquidity_metrics(order_book: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates liquidity metrics from Binance depth data:
    - Bid-Ask Spread %
    - Order Book Imbalance Ratio
    - ±2% Depth
    """
    bids = order_book.get("bids", [])
    asks = order_book.get("asks", [])
    
    if not bids or not asks:
        return {"spread_pct": 0.0, "imbalance": 0.0, "depth_2pct": 0.0}
    
    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    midpoint = (best_bid + best_ask) / 2
    
    spread_pct = ((best_ask - best_bid) / midpoint) * 100 if midpoint != 0 else 0.0
    
    # Calculate Imbalance and Depth
    # Bids/Asks are lists of [price, quantity]
    
    total_bid_vol = sum(float(b[1]) for b in bids)
    total_ask_vol = sum(float(a[1]) for a in asks)
    
    imbalance = total_bid_vol / total_ask_vol if total_ask_vol != 0 else 0.0
    
    # ±2% Depth Calculation
    # We need to sum volume within 2% of mid price
    lower_bound = midpoint * 0.98
    upper_bound = midpoint * 1.02
    
    depth_2pct = 0.0
    
    for price, qty in bids:
        p = float(price)
        if p >= lower_bound:
            depth_2pct += float(qty) * p
        else:
            break # Bids are sorted descending
            
    for price, qty in asks:
        p = float(price)
        if p <= upper_bound:
            depth_2pct += float(qty) * p
        else:
            break # Asks are sorted ascending
            
    return {
        "spread_pct": spread_pct,
        "imbalance": imbalance,
        "depth_2pct": depth_2pct
    }

def calculate_technical_indicators(prices: List[float]) -> Dict[str, Any]:
    """
    Calculates technical indicators:
    - RSI (14-period)
    - SMA (20, 50)
    - Trend Signal
    """
    if not prices or len(prices) < 50:
        # Not enough data for SMA-50
        return {
            "rsi": None,
            "sma_20": None,
            "sma_50": None,
            "trend": "NEUTRAL"
        }
        
    series = pd.Series(prices)
    
    # RSI (14)
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    # Use simple rolling average as requested
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    current_rsi = rsi_series.iloc[-1]
    
    # SMA
    sma_20 = series.rolling(window=20).mean().iloc[-1]
    sma_50 = series.rolling(window=50).mean().iloc[-1]
    current_price = prices[-1]
    
    # Trend Signal
    trend = "NEUTRAL"
    if current_price > sma_20 > sma_50:
        trend = "BULLISH"
    elif current_price < sma_20 < sma_50:
        trend = "BEARISH"
        
    return {
        "rsi": current_rsi if not pd.isna(current_rsi) else None,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "trend": trend
    }
