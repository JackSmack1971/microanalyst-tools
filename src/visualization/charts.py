import plotext as plt
from typing import List

def generate_price_chart(dates: List[str], prices: List[float], title: str = "Price History") -> str:
    """
    Generates an ASCII price chart string.
    
    Args:
        dates: List of date strings (x-axis).
        prices: List of price values (y-axis).
        title: Chart title.
        
    Returns:
        str: Rendered ASCII chart.
    """
    if not dates or not prices:
        return ""
        
    plt.clear_figure()
    plt.theme('clear') # ASCII friendly
    plt.date_form('Y-m-d')
    plt.plotsize(80, 20)
    
    plt.plot(dates, prices)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    
    return plt.build()

def generate_volume_chart(dates: List[str], volumes: List[float], title: str = "Volume History") -> str:
    """
    Generates an ASCII volume chart string.
    
    Args:
        dates: List of date strings (x-axis).
        volumes: List of volume values (y-axis).
        title: Chart title.
        
    Returns:
        str: Rendered ASCII chart.
    """
    if not dates or not volumes:
        return ""
        
    plt.clear_figure()
    plt.theme('clear')
    plt.date_form('Y-m-d')
    plt.plotsize(80, 20)
    
    # Use bar chart for volume if possible, but plotext bar chart might be tricky with many points.
    # For 30-90 days, bar chart is fine if terminal width allows.
    # If too many points, plot is safer.
    if len(dates) > 40:
        plt.plot(dates, volumes)
    else:
        plt.bar(dates, volumes)
        
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Volume (USD)")
    
    return plt.build()
