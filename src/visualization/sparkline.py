from typing import List

def generate_sparkline(data: List[float], length: int = 10) -> str:
    """
    Generates a unicode sparkline from a list of floats.
    
    Args:
        data: List of float values.
        length: Length of the sparkline in characters.
        
    Returns:
        str: Unicode sparkline string (optionally with Rich color markup).
    """
    if not data:
        return ""
    
    # Downsample data to fit length
    # Simple sampling: take every Nth element or average chunks
    # For sparklines, simple sampling is usually sufficient for visual trend
    if len(data) > length:
        step = len(data) / length
        sampled = [data[int(i * step)] for i in range(length)]
    else:
        # Pad if too short? Or just show what we have?
        # Let's just use what we have if short, or interpolate.
        # For simplicity, if short, just use it.
        sampled = data
        
    min_val = min(sampled)
    max_val = max(sampled)
    range_val = max_val - min_val
    
    levels = u" ▂▃▄▅▆▇█"
    spark = ""
    
    if range_val == 0:
        # Flat line (middle)
        spark = levels[3] * len(sampled)
    else:
        for v in sampled:
            # Normalize to 0-7
            idx = int((v - min_val) / range_val * (len(levels) - 1))
            spark += levels[idx]
            
    # Color coding
    if sampled[-1] > sampled[0]:
        color = "green"
    elif sampled[-1] < sampled[0]:
        color = "red"
    else:
        color = "white"
        
    return f"[{color}]{spark}[/{color}]"
