import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

def calculate_risk_metrics(prices: List[float], risk_free_rate: float = 0.0) -> Dict[str, Optional[float]]:
    """
    Calculates risk-adjusted return metrics.
    
    Args:
        prices: List of historical prices (ordered by time).
        risk_free_rate: Annualized risk-free rate (default 0.0 for crypto).
        
    Returns:
        Dictionary containing:
        - max_drawdown: Maximum percentage drop from peak.
        - sharpe_ratio: Annualized Sharpe Ratio.
        - sortino_ratio: Annualized Sortino Ratio.
    """
    if not prices or len(prices) < 2:
        return {
            "max_drawdown": None,
            "sharpe_ratio": None,
            "sortino_ratio": None
        }
        
    prices_series = pd.Series(prices)
    returns = prices_series.pct_change().dropna()
    
    if returns.empty or returns.std() == 0:
        return {
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0
        }

    # Max Drawdown
    peak = prices_series.expanding(min_periods=1).max()
    drawdown = (prices_series - peak) / peak
    max_drawdown = drawdown.min()
    
    # Annualization factor (crypto trades 365 days)
    annual_factor = np.sqrt(365)
    
    # Sharpe Ratio
    excess_returns = returns - (risk_free_rate / 365)
    sharpe_ratio = (excess_returns.mean() / returns.std()) * annual_factor
    
    # Sortino Ratio
    downside_returns = returns[returns < 0]
    if downside_returns.empty or downside_returns.std() == 0:
        sortino_ratio = float('inf') if returns.mean() > 0 else 0.0
    else:
        sortino_ratio = (excess_returns.mean() / downside_returns.std()) * annual_factor
        
    return {
        "max_drawdown": float(max_drawdown),
        "sharpe_ratio": float(sharpe_ratio),
        "sortino_ratio": float(sortino_ratio)
    }

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
    """
    Calculates MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: List of historical prices.
        fast: Fast EMA period.
        slow: Slow EMA period.
        signal: Signal line EMA period.
        
    Returns:
        Dictionary containing the latest:
        - macd_line
        - signal_line
        - histogram
    """
    if not prices or len(prices) < slow:
        return {
            "macd_line": None,
            "signal_line": None,
            "histogram": None
        }
        
    prices_series = pd.Series(prices)
    
    # Calculate EMAs
    ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
    ema_slow = prices_series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        "macd_line": float(macd_line.iloc[-1]),
        "signal_line": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1])
    }

def calculate_fibonacci_levels(prices: List[float]) -> Dict[str, float]:
    """
    Calculates Fibonacci retracement levels based on the high and low of the period.
    
    Args:
        prices: List of historical prices.
        
    Returns:
        Dictionary of levels: 0.236, 0.382, 0.5, 0.618, 0.786
    """
    if not prices:
        return {}
        
    high = max(prices)
    low = min(prices)
    diff = high - low
    
    return {
        "fib_0.236": high - (diff * 0.236),
        "fib_0.382": high - (diff * 0.382),
        "fib_0.500": high - (diff * 0.5),
        "fib_0.618": high - (diff * 0.618),
        "fib_0.786": high - (diff * 0.786),
        "high": high,
        "low": low
    }
