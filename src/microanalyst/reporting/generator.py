from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.console import Group, RenderableType
from rich.bar import Bar
from rich import box
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
    vol_delta_val = metrics["volume_delta"]
    risk_table = generate_risk_table(metrics)

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
    """
    table = Table(title="Quantitative Metrics", border_style="blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Signal", justify="center")
    
    metric_defs = [
        ("Volatility (CV)", "volatility", lambda v: format_number(v, 2)),
        ("Spread", "spread", lambda v: format_percentage(v / 100.0, 2)),
        ("Volume Delta", "volume_delta", lambda v: format_percentage(v / 100.0, 1)),
        ("Imbalance", "imbalance", lambda v: format_number(v, 2))
    ]
    
    for label, metric_type, formatter in metric_defs:
        value = metrics.get(metric_type)
        if value is None:
            continue
            
        formatted_val = formatter(value)
        color = get_metric_color(metric_type, value)
        
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
    """
    name = token_data.get("name", "Unknown")
    symbol = token_data.get("symbol", "???").upper()
    rank = token_data.get("market_cap_rank")
    
    market_data = token_data.get("market_data", {})
    price = market_data.get("current_price", {}).get("usd")
    market_cap = market_data.get("market_cap", {}).get("usd")
    volume_24h = market_data.get("total_volume", {}).get("usd")
    
    rank_color = "green" if rank and rank <= 10 else "yellow" if rank and rank > 100 else "cyan"
    rank_str = f"#{rank}" if rank else "N/A"
    
    left_content = Group(
        Text(f"{symbol}", style="bold white"),
        Text(f"{name}", style="white"),
        Text(f"Rank: ", style="dim") + Text(rank_str, style=rank_color)
    )
    
    right_content = Group(
        Text(f"Price: {format_currency(price)}", style="bold green"),
        Text(f"MCap:  {format_currency(market_cap)}", style="cyan"),
        Text(f"Vol24: {format_currency(volume_24h)}", style="blue")
    )
    
    columns = Columns([left_content, right_content], expand=True)
    
    return Panel(
        columns,
        title="TOKEN OVERVIEW",
        border_style="cyan",
        width=80
    )

def generate_comparison_table(metrics_df: pd.DataFrame) -> Table:
    """
    Generates a Rich Table comparing multiple tokens.
    
    Args:
        metrics_df: DataFrame containing comparison metrics.
        
    Returns:
        Table: Rich Table object.
    """
    if metrics_df.empty:
        return Table(title="Comparison Matrix (Empty)")
        
    table = Table(title="Token Comparison Matrix", border_style="magenta", box=box.SIMPLE)
    
    # Add columns dynamically based on DataFrame columns
    for col in metrics_df.columns:
        if col == "Symbol":
            table.add_column(col, style="bold cyan")
        else:
            table.add_column(col, justify="right")
            
    # Add rows
    for _, row in metrics_df.iterrows():
        row_data = []
        for col in metrics_df.columns:
            val = row[col]
            # Basic formatting
            if isinstance(val, float):
                if "Price" in col or "Cap" in col or "Volume" in col:
                     # Heuristic for large numbers
                     if val > 1000:
                         fmt_val = f"${val:,.0f}"
                     else:
                         fmt_val = f"${val:,.2f}"
                elif "%" in col:
                     fmt_val = f"{val:.2f}%"
                else:
                     fmt_val = f"{val:.2f}"
            else:
                fmt_val = str(val)
            row_data.append(fmt_val)
        table.add_row(*row_data)
        
    return table

def generate_correlation_table(correlation_df: pd.DataFrame) -> Table:
    """
    Generates a correlation matrix heatmap table.
    
    Args:
        correlation_df: DataFrame containing correlation coefficients.
        
    Returns:
        Rich Table object.
    """
    table = Table(title="Market Correlation Heatmap (Pearson)", box=box.SIMPLE)
    
    # Add columns (Token Symbols)
    table.add_column("Token", style="bold cyan")
    for col in correlation_df.columns:
        table.add_column(col, justify="right")
        
    # Add rows
    for index, row in correlation_df.iterrows():
        row_data = [str(index)] # First cell is the token symbol (index)
        
        for val in row:
            # Conditional Formatting
            if val > 0.8 and val < 1.0: # High positive correlation (excluding self-correlation)
                style = "[red]"
            elif val < 0.0: # Negative correlation (hedge)
                style = "[green]"
            else:
                style = ""
                
            formatted_val = f"{style}{val:.2f}[/]"
            row_data.append(formatted_val)
            
        table.add_row(*row_data)
        
    return table

def generate_risk_table(metrics: Dict[str, float]) -> Table:
    """
    Generates a Risk Factors table based on metrics.
    """
    risks = []
    spread_val = metrics.get("spread")
    spread_val = spread_val if spread_val is not None else 0.0
    
    vol_delta_val = metrics.get("volume_delta", 0.0)
    
    imbalance_val = metrics.get("imbalance")
    imbalance_val = imbalance_val if imbalance_val is not None else 1.0
    
    if spread_val > 0.5:
        risks.append(("[bold red]Wide Bid-Ask Spread[/bold red]", f"{spread_val:.2f}%"))
        
    if vol_delta_val > 20:
        risks.append(("[bold yellow]Volume Discrepancy[/bold yellow]", f"{vol_delta_val:.1f}%"))
        
    if imbalance_val < 0.5 or imbalance_val > 2.0:
        risks.append(("[bold magenta]Order Book Imbalance[/bold magenta]", f"{imbalance_val:.2f}"))
        
    table = Table(title="Risk Factors", border_style="red", show_header=True)
    table.add_column("Risk Type", style="bold")
    table.add_column("Value")
    
    if risks:
        for r_type, r_val in risks:
            table.add_row(r_type, r_val)
    else:
        table.add_row("[green]No critical risks detected[/green]", "-")
        
    return table
