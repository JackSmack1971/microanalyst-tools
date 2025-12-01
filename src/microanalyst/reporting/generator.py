from datetime import datetime
from typing import Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.console import Group
from src.cli.theme import get_metric_color, SEVERITY_STYLES
from src.cli.formatters import format_percentage, format_currency, format_number

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

def generate_metric_table(metrics: Dict[str, float]) -> Table:
    """
    Generates a Rich Table for quantitative metrics with semantic coloring.
    
    Args:
        metrics: Dictionary of metric values (e.g., {'volatility': 0.15, 'spread': 0.005})
        
    Returns:
        Table: Rich Table object ready for rendering.
    """
    table = Table(title="Quantitative Metrics", border_style="blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Signal", justify="center")
    
    # Define metrics to display and their formatting logic
    # Key: (Display Name, Metric Type for Theme, Formatter)
    metric_defs = [
        ("Volatility (CV)", "volatility", lambda v: format_number(v, 2)),
        ("Spread", "spread", lambda v: format_percentage(v / 100.0, 2)),
        ("Volume Delta", "volume_delta", lambda v: format_percentage(v / 100.0, 1)),
        ("Imbalance", "imbalance", lambda v: format_number(v, 2))
    ]
    
    # Note on Volume Delta: In main.py, it is calculated as percentage (e.g. 50.0 for 50%).
    # format_percentage expects ratio (0.5 for 50%).
    # So we need to divide by 100 if it's a percentage > 1? Or just assume it's a percentage?
    # Let's look at main.py: `vol_delta = ((abs(cg_vol - bin_vol)) / cg_vol * 100)` -> returns 0..100+
    # So we should divide by 100 for format_percentage.
    
    # Note on Spread: In main.py: `spread = f"{liquidity_metrics.get('spread_pct', 0.0):.2f}%"`
    # If spread_pct is 0.5 (meaning 0.5%), then format_percentage(0.5) -> 50%. That's wrong.
    # If spread_pct is 0.005 (meaning 0.5%), then format_percentage(0.005) -> 0.50%.
    # We need to know what the metrics actually contain.
    # main.py: `liquidity_metrics = calculate_liquidity_metrics(depth)`
    # We don't see the implementation of calculate_liquidity_metrics.
    # However, standard practice: spread is usually small.
    # Let's assume the metrics passed to this function are RAW values.
    # If main.py formats them as f"{val:.2f}%", it implies val is 0.5 for 0.5%? No, usually 0.5 means 50% in f-string unless it's just a number.
    # Wait, f"{0.5:.2f}%" -> "0.50%".
    # So if spread is 0.5, it prints "0.50%".
    # So spread is likely in percentage points (0.5 = 0.5%).
    # format_percentage(0.5) -> "50.00%".
    # So we need to divide spread by 100 too if we use format_percentage?
    # OR we just use format_number and add % manually?
    # formatters.format_percentage expects ratio.
    # Let's stick to format_percentage(v/100) if v is in percentage points.
    
    for label, metric_type, formatter in metric_defs:
        value = metrics.get(metric_type)
        if value is None:
            continue
            
        # Special handling for percentage inputs vs ratios
        # We'll assume metrics are passed as they are in main.py (likely percentage points for some)
        # But for safety in this specific task, let's look at theme.py thresholds.
        # Volatility: high 0.12. This looks like a ratio (12%).
        # Spread: high 0.5. This looks like percentage points (0.5%).
        # Volume Delta: critical 50.0. This looks like percentage points (50%).
        
        # So:
        # Volatility: Ratio. format_number(0.12) -> 0.12. Correct.
        # Spread: Percentage Points. format_percentage(0.5/100) -> 0.50%.
        # Volume Delta: Percentage Points. format_percentage(50/100) -> 50.00%.
        
        formatted_val = "N/A"
        formatted_val = formatter(value)

        color = get_metric_color(metric_type, value)
        
        # Determine signal icon
        signal = ""
        if color == SEVERITY_STYLES["critical"]:
            signal = "⚠️ HIGH"
        elif color == SEVERITY_STYLES["warning"]:
            signal = "⚠️ WARN"
        elif color == SEVERITY_STYLES["healthy"]:
            signal = "✓ OK"
        else:
            signal = "-"
            
        table.add_row(label, f"[{color}]{formatted_val}[/{color}]", f"[{color}]{signal}[/{color}]")
        
    return table

def generate_overview_panel(token_data: Dict[str, Any]) -> Panel:
    """
    Generates a structured Token Overview panel.
    
    Args:
        token_data: CoinGecko token data dictionary.
        
    Returns:
        Panel: Rich Panel object.
    """
    # Extract Data
    name = token_data.get("name", "Unknown")
    symbol = token_data.get("symbol", "???").upper()
    rank = token_data.get("market_cap_rank")
    
    market_data = token_data.get("market_data", {})
    price = market_data.get("current_price", {}).get("usd")
    market_cap = market_data.get("market_cap", {}).get("usd")
    volume_24h = market_data.get("total_volume", {}).get("usd")
    
    # Left Column: Identity
    rank_color = "green" if rank and rank <= 10 else "yellow" if rank and rank > 100 else "cyan"
    rank_str = f"#{rank}" if rank else "N/A"
    
    left_content = Group(
        Text(f"{symbol}", style="bold white"),
        Text(f"{name}", style="white"),
        Text(f"Rank: ", style="dim") + Text(rank_str, style=rank_color)
    )
    
    # Right Column: Market Data
    right_content = Group(
        Text(f"Price: {format_currency(price)}", style="bold green"),
        Text(f"MCap:  {format_currency(market_cap)}", style="cyan"),
        Text(f"Vol24: {format_currency(volume_24h)}", style="blue")
    )
    
    # Layout
    columns = Columns([left_content, right_content], expand=True)
    
    return Panel(
        columns,
        title="TOKEN OVERVIEW",
        border_style="cyan",
        width=80
    )


