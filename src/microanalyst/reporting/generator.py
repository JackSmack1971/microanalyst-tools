from datetime import datetime
from typing import Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.console import Group, RenderableType
from rich.bar import Bar
from src.cli.theme import get_metric_color, SEVERITY_STYLES
from src.cli.formatters import format_percentage, format_currency, format_number

def generate_report(
    token_symbol: str,
    cg_data: Dict[str, Any],
    binance_ticker: Dict[str, Any],
    volatility_metrics: Dict[str, float],
    volume_metrics: Dict[str, float],
    liquidity_metrics: Dict[str, float],
    validation_flags: Dict[str, Any],
    config: Dict[str, Any] = None
) -> RenderableType:
    """
    Generates the Standard Analysis Report as a Rich Renderable Group.
    """
    if config is None:
        config = {}
        
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # 1. Overview Panel
    overview_panel = generate_overview_panel(cg_data)
    
    # 2. Metrics Table
    # Prepare metrics dictionary for the table generator
    metrics = {
        "volatility": volatility_metrics.get("cv"),
        "spread": liquidity_metrics.get("spread_pct"),
        "volume_delta": ((abs(cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 0) - float(binance_ticker.get("quoteVolume", 0)))) / cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 1) * 100) if cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 0) else 0.0,
        "imbalance": liquidity_metrics.get("imbalance")
    }
    metric_table = generate_metric_table(metrics)
    
    # 3. Risk Factors
    # Recalculate risk factors for display (logic similar to original string generation but structured)
    risks = []
    spread_val = metrics["spread"] if metrics["spread"] is not None else 0.0
    vol_delta_val = metrics["volume_delta"]
    imbalance_val = metrics["imbalance"] if metrics["imbalance"] is not None else 1.0
    
    # Spread Risk
    # Note: spread is percentage points (e.g. 0.5 for 0.5%)
    if spread_val > 0.5:
        risks.append(("[bold red]Wide Bid-Ask Spread[/bold red]", f"{spread_val:.2f}%"))
        
    # Volume Delta Risk
    if vol_delta_val > 20:
        risks.append(("[bold yellow]Volume Discrepancy[/bold yellow]", f"{vol_delta_val:.1f}%"))
        
    # Imbalance Risk
    if imbalance_val < 0.5 or imbalance_val > 2.0:
        risks.append(("[bold magenta]Order Book Imbalance[/bold magenta]", f"{imbalance_val:.2f}"))
        
    risk_table = Table(title="Risk Factors", border_style="red", show_header=True)
    risk_table.add_column("Risk Type", style="bold")
    risk_table.add_column("Value")
    
    if risks:
        for r_type, r_val in risks:
            risk_table.add_row(r_type, r_val)
    else:
        risk_table.add_row("[green]No critical risks detected[/green]", "-")

    # 4. Footer / Confidence
    confidence_score = 100.0
    if vol_delta_val > 50:
        confidence_score = 40.0
    elif vol_delta_val > 20:
        confidence_score = 70.0
        
    footer = Group(
        Text(f"\nAnalysis Timestamp: {timestamp}", style="dim"),
        Text("Data Confidence:", style="bold"),
        Bar(100, 0, 100, width=40, color="green" if confidence_score > 80 else "yellow")
    )
    
    return Group(
        overview_panel,
        Text(""), # Spacer
        metric_table,
        Text(""), # Spacer
        risk_table,
        footer
    )

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

def generate_comparison_table(comparison_data: Dict[str, Any]) -> Table:
    """
    Generates a Rich Table comparing multiple tokens.
    
    Args:
        comparison_data: Output from comparator.compare_tokens.
        
    Returns:
        Table: Rich Table object.
    """
    matrix = comparison_data.get("comparison_matrix", [])
    stats = comparison_data.get("summary_stats", {})
    
    if not matrix:
        return Table(title="Comparison Matrix (Empty)")
        
    # Determine metrics from stats keys
    metrics = list(stats.keys())
    
    # Create Table
    table = Table(title="Token Comparison Matrix", border_style="magenta")
    table.add_column("Metric", style="cyan")
    
    # Add columns for each token
    tokens = [item.get("symbol", f"Token_{i}") for i, item in enumerate(matrix)]
    for token in tokens:
        table.add_column(token, justify="right")
        
    table.add_column("Avg", justify="right", style="dim")
    table.add_column("StdDev", justify="right", style="dim")
    
    # Add rows for each metric
    for metric in metrics:
        row_data = [metric.replace("_", " ").title()]
        
        # Get stats
        mean = stats[metric]["mean"]
        std = stats[metric]["std"]
        
        # Add token values with coloring
        for item in matrix:
            val = item.get(metric)
            z_score = item.get(f"{metric}_z_score", 0.0)
            
            # Formatting
            if isinstance(val, (int, float)):
                fmt_val = format_number(val, 2)
            else:
                fmt_val = str(val)
                
            # Coloring based on Z-Score (Simple heuristic: > 1 std dev is colored)
            # Polarity is ambiguous without metadata, so we just highlight deviation
            color = ""
            if z_score > 1.0:
                color = "yellow"
            elif z_score < -1.0:
                color = "blue"
            elif z_score > 2.0:
                color = "red"
                
            if color:
                fmt_val = f"[{color}]{fmt_val}[/{color}]"
                
            row_data.append(fmt_val)
            
        # Add stats
        row_data.append(format_number(mean, 2))
        row_data.append(format_number(std, 2))
        
        table.add_row(*row_data)
        
    return table


