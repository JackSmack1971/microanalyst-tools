import pandas as pd
import numpy as np
from typing import List, Dict, Any

def compare_tokens(tokens: List[Dict[str, Any]], metrics: List[str]) -> Dict[str, Any]:
    """
    Compare multiple tokens based on a list of metrics.

    Args:
        tokens: List of dictionaries containing token data.
                Each dict must have 'symbol' and keys corresponding to metrics.
        metrics: List of metric keys to compare (e.g., ['volatility', 'spread']).

    Returns:
        Dictionary containing:
        - comparison_matrix: List of dicts with original data + stats (z_score, percentile, deviation).
        - summary_stats: Dictionary of summary statistics for each metric.
    """
    if not tokens:
        return {"comparison_matrix": [], "summary_stats": {}}

    # Convert to DataFrame
    df = pd.DataFrame(tokens)
    
    # Ensure 'symbol' is present, if not, use index
    if 'symbol' not in df.columns:
        df['symbol'] = [f"Token_{i}" for i in range(len(df))]

    # Filter for relevant metrics and ensure numeric
    # We only process metrics that exist in the dataframe columns
    valid_metrics = [m for m in metrics if m in df.columns]
    
    if not valid_metrics:
        # Return basic info if no metrics found
        return {
            "comparison_matrix": df.to_dict(orient='records'),
            "summary_stats": {}
        }

    metric_df = df[valid_metrics].apply(pd.to_numeric, errors='coerce')
    
    # Calculate Summary Stats
    summary_stats = metric_df.describe().to_dict()
    
    # Calculate Derived Stats
    results = df.copy()
    
    for metric in valid_metrics:
        series = metric_df[metric]
        mean = series.mean()
        std = series.std()
        
        # Deviation from Mean (%)
        # Handle division by zero if mean is 0
        if mean != 0:
            results[f"{metric}_dev_pct"] = ((series - mean) / abs(mean) * 100).fillna(0.0)
        else:
            results[f"{metric}_dev_pct"] = 0.0
        
        # Z-Score
        if std > 0:
            results[f"{metric}_z_score"] = ((series - mean) / std).fillna(0.0)
        else:
            results[f"{metric}_z_score"] = 0.0
            
        # Percentile Rank (0-100)
        results[f"{metric}_percentile"] = series.rank(pct=True) * 100

    # Convert back to list of dicts
    # Replace NaN with None for JSON compliance if needed, or keep as is.
    # Pandas to_dict handles NaNs as NaN (which is invalid JSON but valid Python float).
    # For safety, let's replace NaN with None
    results = results.replace({np.nan: None})
    
    comparison_matrix = results.to_dict(orient='records')
    
    return {
        "comparison_matrix": comparison_matrix,
        "summary_stats": summary_stats
    }
