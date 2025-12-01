import sys
import argparse
import logging
from typing import Dict, Any, List, Optional
import logging
from enum import Enum
from rich.console import Console
from rich.markdown import Markdown
from rich.logging import RichHandler
from rich.traceback import install
from src.cli.theme import generate_error_panel, get_metric_color, SEVERITY_STYLES
from src.cli.progress import create_progress_bar, STAGE_DESCRIPTIONS
from src.cli.formatters import format_number, format_percentage, format_currency
from src.cli.prompts import prompt_token_selection
from src.export.json_exporter import export_to_json
from src.export.html_exporter import export_to_html
from src.config.loader import load_config
from pathlib import Path
from datetime import datetime
import questionary

from src.microanalyst.providers.coingecko import CoinGeckoClient
from src.microanalyst.providers.binance import BinanceClient
from src.microanalyst.analysis.metrics import (
    calculate_volatility_metrics,
    calculate_volume_metrics,
    calculate_liquidity_metrics
)
from src.comparison.comparator import compare_tokens
from src.microanalyst.reporting.generator import generate_report, generate_comparison_table
from src.visualization.charts import generate_price_chart, generate_volume_chart

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("microanalyst")
install(show_locals=False)
console = Console()

class OutputMode(str, Enum):
    TERMINAL = "terminal"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"

def analyze_token(token_symbol: str, cg_client: CoinGeckoClient, binance_client: BinanceClient, days: int, progress=None, task_ids=None) -> Dict[str, Any]:
    """
    Analyzes a single token and returns all relevant data and metrics.
    """
    # Search
    if progress and task_ids:
        progress.update(task_ids["search"], advance=0, description=f"Searching {token_symbol}...")
        
    try:
        search_results = cg_client.search(token_symbol)
    except Exception as e:
        logger.error(f"Search failed for {token_symbol}: {e}")
        return None
    
    if not search_results or not search_results.get("coins"):
        logger.error(f"Token {token_symbol} not found.")
        return None
    
    # Default behavior: pick first
    token_id = search_results["coins"][0]["id"]
    token_symbol_api = search_results["coins"][0]["symbol"]
    
    if progress and task_ids:
        progress.update(task_ids["search"], advance=1)
        progress.update(task_ids["market"], advance=0, description=f"Fetching data for {token_symbol_api}...")

    # Fetch Market Data
    try:
        cg_data = cg_client.get_token_data(token_id)
        market_chart = cg_client.get_market_chart(token_id, days=days)
    except Exception as e:
        logger.error(f"Data fetch failed for {token_id}: {e}")
        return None
    
    if not cg_data or not market_chart:
        return None
        
    if progress and task_ids:
        progress.update(task_ids["market"], advance=1)
        progress.update(task_ids["orderbook"], advance=0, description=f"Fetching orderbook for {token_symbol_api}...")

    # Binance Data
    binance_symbol = f"{token_symbol_api.upper()}USDT"
    ticker_24h = binance_client.get_ticker_24h(binance_symbol)
    depth = binance_client.get_depth(binance_symbol)
    
    if not ticker_24h:
        ticker_24h = {}
        depth = {"bids": [], "asks": []}
        
    if progress and task_ids:
        progress.update(task_ids["orderbook"], advance=1)
        progress.update(task_ids["analysis"], advance=0, description=f"Analyzing {token_symbol_api}...")

    # Analyze
    prices_data = market_chart.get("prices", [])
    volumes_data = market_chart.get("total_volumes", [])
    
    prices = [p[1] for p in prices_data]
    volumes = [v[1] for v in volumes_data]
    
    # Extract dates for charts (convert ms timestamp to datetime string)
    # CoinGecko timestamps are in ms
    dates = [datetime.fromtimestamp(p[0]/1000).strftime("%Y-%m-%d") for p in prices_data]
    
    volatility_metrics = calculate_volatility_metrics(prices)
    volume_metrics = calculate_volume_metrics(prices, volumes)
    liquidity_metrics = calculate_liquidity_metrics(depth)
    
    # Calculate derived values
    cg_vol = cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 0)
    bin_vol = float(ticker_24h.get("quoteVolume", 0))
    vol_delta = ((abs(cg_vol - bin_vol)) / cg_vol * 100) if cg_vol else 0.0
    
    if progress and task_ids:
        progress.update(task_ids["analysis"], advance=1)

    return {
        "token_symbol": token_symbol,
        "token_symbol_api": token_symbol_api,
        "cg_data": cg_data,
        "ticker_24h": ticker_24h,
        "volatility_metrics": volatility_metrics,
        "volume_metrics": volume_metrics,
        "liquidity_metrics": liquidity_metrics,
        "vol_delta": vol_delta,
        # Flattened metrics for comparison
        "volatility": volatility_metrics.get("cv"),
        "spread": liquidity_metrics.get("spread_pct"),
        "volume_delta": vol_delta,
        "imbalance": liquidity_metrics.get("imbalance"),
        # Chart data
        "dates": dates,
        "prices": prices,
        "volumes": volumes
    }

def main():
    parser = argparse.ArgumentParser(description="Elite Cryptocurrency Microanalyst Tool")
    parser.add_argument("token", nargs="?", help="Token symbol (e.g., btc, eth, sol)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive mode")
    parser.add_argument("--days", help="Days of historical data (default: 30)")
    parser.add_argument(
        "--output",
        choices=[m.value for m in OutputMode],
        help="Output format (default: terminal)"
    )
    parser.add_argument("--save", help="Custom output filepath (optional)")
    parser.add_argument("--config", help="Path to custom configuration file")
    parser.add_argument("--compare", help="Comma-separated list of tokens to compare (2-10)")
    parser.add_argument("--charts", action="store_true", help="Display price and volume charts")
    args = parser.parse_args()

    # Load Config
    try:
        config_path = Path(args.config) if args.config else None
        config = load_config(config_path)
        console.print(f"[dim]Loaded configuration from {config_path or 'defaults'}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load config: {e}. Using internal defaults.[/yellow]")
        config = load_config()

    # Apply defaults
    days = int(args.days) if args.days else config["defaults"]["days"]
    output_mode_str = args.output if args.output else config["defaults"]["output_format"]
    output_mode = OutputMode(output_mode_str)
    
    # Initialize Clients
    cg_client = CoinGeckoClient()
    binance_client = BinanceClient()

    # --- COMPARISON MODE ---
    if args.compare:
        tokens = [t.strip() for t in args.compare.split(",") if t.strip()]
        if len(tokens) < 2:
            console.print(generate_error_panel("Input Error", "Comparison requires at least 2 tokens.", []))
            return
        if len(tokens) > 10:
            console.print(generate_error_panel("Input Error", "Comparison limited to 10 tokens max.", []))
            return
            
        console.print(f"[bold blue]Comparing {len(tokens)} tokens...[/bold blue]")
        
        results = []
        with create_progress_bar() as progress:
            task_search = progress.add_task(STAGE_DESCRIPTIONS["token_search"], total=len(tokens))
            task_market = progress.add_task(STAGE_DESCRIPTIONS["market_data"], total=len(tokens))
            task_orderbook = progress.add_task(STAGE_DESCRIPTIONS["orderbook"], total=len(tokens))
            task_analysis = progress.add_task(STAGE_DESCRIPTIONS["analysis"], total=len(tokens))
            
            task_ids = {
                "search": task_search,
                "market": task_market,
                "orderbook": task_orderbook,
                "analysis": task_analysis
            }
            
            for token in tokens:
                data = analyze_token(token, cg_client, binance_client, days, progress, task_ids)
                if data:
                    data["symbol"] = data["token_symbol_api"].upper()
                    results.append(data)
                else:
                    console.print(f"[yellow]Skipping {token} (failed to analyze)[/yellow]")
                    
        if len(results) < 2:
            console.print(generate_error_panel("Comparison Failed", "Not enough valid tokens to compare.", []))
            return
            
        # Compare
        metrics_to_compare = ["volatility", "spread", "volume_delta", "imbalance"]
        comparison_data = compare_tokens(results, metrics_to_compare)
        
        # Render Table
        table = generate_comparison_table(comparison_data)
        console.print(table)
        
        # Render Charts if requested
        if args.charts:
            console.print("\n[bold cyan]Generating Charts...[/bold cyan]")
            for res in results:
                console.print(f"\n[bold underline]{res['symbol']} Charts[/bold underline]")
                p_chart = generate_price_chart(res["dates"], res["prices"], f"{res['symbol']} Price History")
                v_chart = generate_volume_chart(res["dates"], res["volumes"], f"{res['symbol']} Volume History")
                console.print(p_chart)
                console.print(v_chart)
        return

    # --- SINGLE TOKEN MODE ---
    is_interactive = args.interactive and sys.stdout.isatty()
    search_query = args.token
    
    if not search_query:
        if is_interactive:
            try:
                search_query = questionary.text("Enter token symbol or name to search:").ask()
                if not search_query:
                    console.print("[yellow]Search cancelled.[/yellow]")
                    return
            except KeyboardInterrupt:
                return
        else:
            parser.error("the following arguments are required: token (or use --interactive)")

    token_symbol = search_query.lower()
    console.print(f"[bold blue]Starting analysis for {token_symbol.upper()}...[/bold blue]")

    resolved_token_symbol = token_symbol
    
    if is_interactive:
        with create_progress_bar() as progress:
             task_search = progress.add_task(STAGE_DESCRIPTIONS["token_search"], total=1)
             try:
                 search_results = cg_client.search(token_symbol)
                 progress.update(task_search, advance=1)
             except Exception:
                 search_results = None
                 
        if search_results and search_results.get("coins"):
             selected_id = prompt_token_selection(search_results["coins"])
             if not selected_id:
                 return
             selected_coin = next((c for c in search_results["coins"] if c["id"] == selected_id), None)
             if selected_coin:
                 resolved_token_symbol = selected_coin["symbol"]
    
    # Run Analysis
    with create_progress_bar() as progress:
        task_search = progress.add_task(STAGE_DESCRIPTIONS["token_search"], total=1)
        task_market = progress.add_task(STAGE_DESCRIPTIONS["market_data"], total=1)
        task_orderbook = progress.add_task(STAGE_DESCRIPTIONS["orderbook"], total=1)
        task_analysis = progress.add_task(STAGE_DESCRIPTIONS["analysis"], total=1)
        
        task_ids = {
            "search": task_search,
            "market": task_market,
            "orderbook": task_orderbook,
            "analysis": task_analysis
        }
        
        data = analyze_token(resolved_token_symbol, cg_client, binance_client, days, progress, task_ids)
        
    if not data:
        return

    # 3. Report / Export
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    report_data = {
        "token_symbol": data["token_symbol"],
        "timestamp": timestamp,
        "overview": {
            "name": data["cg_data"].get("name", "Unknown"),
            "symbol": data["cg_data"].get("symbol", "???"),
            "rank": data["cg_data"].get("market_cap_rank"),
            "price": format_currency(data["cg_data"].get("market_data", {}).get("current_price", {}).get("usd")),
            "market_cap": format_currency(data["cg_data"].get("market_data", {}).get("market_cap", {}).get("usd")),
            "volume_24h": format_currency(data["cg_data"].get("market_data", {}).get("total_volume", {}).get("usd", 0))
        },
        "metrics": [],
        "risks": [],
        "confidence_score": 100
    }
    
    # Populate metrics list
    raw_metrics = {
        "volatility": data["volatility"],
        "spread": data["spread"],
        "volume_delta": data["volume_delta"],
        "imbalance": data["imbalance"]
    }
    
    metric_labels = {
        "volatility": "Volatility (CV)",
        "spread": "Spread",
        "volume_delta": "Volume Delta",
        "imbalance": "Imbalance"
    }
    
    for key, val in raw_metrics.items():
        if val is not None:
            color = get_metric_color(key, val)
            signal = "OK"
            signal_class = "signal-ok"
            if color == SEVERITY_STYLES["critical"]:
                signal = "HIGH"
                signal_class = "signal-high"
            elif color == SEVERITY_STYLES["warning"]:
                signal = "WARN"
                signal_class = "signal-warn"
            
            fmt_val = str(val)
            if key == "volatility": fmt_val = format_number(val, 2)
            elif key == "spread": fmt_val = format_percentage(val / 100.0, 2)
            elif key == "volume_delta": fmt_val = format_percentage(val / 100.0, 1)
            elif key == "imbalance": fmt_val = format_number(val, 2)

            report_data["metrics"].append({
                "name": metric_labels.get(key, key),
                "value": fmt_val,
                "signal": signal,
                "signal_class": signal_class
            })

    # Populate risks
    spread_val = raw_metrics["spread"] or 0.0
    imbalance_val = raw_metrics["imbalance"] or 1.0
    vol_delta = raw_metrics["volume_delta"] or 0.0
    
    if spread_val > 0.5:
        report_data["risks"].append({"type": "Wide Bid-Ask Spread", "value": f"{spread_val:.2f}%"})
    if vol_delta > 20:
        report_data["risks"].append({"type": "Volume Discrepancy", "value": f"{vol_delta:.1f}%"})
    if imbalance_val < 0.5 or imbalance_val > 2.0:
        report_data["risks"].append({"type": "Order Book Imbalance", "value": f"{imbalance_val:.2f}"})

    # Confidence Score
    if vol_delta > 50:
        report_data["confidence_score"] = 40
    elif vol_delta > 20:
        report_data["confidence_score"] = 70

    # Routing
    if output_mode == OutputMode.TERMINAL:
        report_renderable = generate_report(
            data["token_symbol"],
            data["cg_data"],
            data["ticker_24h"],
            data["volatility_metrics"],
            data["volume_metrics"],
            data["liquidity_metrics"],
            validation_flags={},
            config=config
        )
        console.print(report_renderable)
        
        # Render Charts if requested
        if args.charts:
            console.print("\n[bold cyan]Generating Charts...[/bold cyan]")
            p_chart = generate_price_chart(data["dates"], data["prices"], f"{data['token_symbol_api'].upper()} Price History")
            v_chart = generate_volume_chart(data["dates"], data["volumes"], f"{data['token_symbol_api'].upper()} Volume History")
            console.print(p_chart)
            console.print(v_chart)
        
    else:
        if args.save:
            filepath = Path(args.save)
        else:
            date_str = datetime.utcnow().strftime("%Y%m%d")
            ext = "json" if output_mode == OutputMode.JSON else "html"
            filepath = Path(f"{data['token_symbol']}_{date_str}.{ext}")
            
        try:
            if output_mode == OutputMode.JSON:
                export_to_json(report_data, filepath)
            elif output_mode == OutputMode.HTML:
                export_to_html(report_data, filepath)
            elif output_mode == OutputMode.MARKDOWN:
                 console.print("[yellow]Markdown export not yet implemented as file. Printing to terminal.[/yellow]")
                 report_renderable = generate_report(
                    data["token_symbol"],
                    data["cg_data"],
                    data["ticker_24h"],
                    data["volatility_metrics"],
                    data["volume_metrics"],
                    data["liquidity_metrics"],
                    validation_flags={},
                    config=config
                )
                 console.print(report_renderable)
                 if args.charts:
                    console.print("\n[bold cyan]Generating Charts...[/bold cyan]")
                    p_chart = generate_price_chart(data["dates"], data["prices"], f"{data['token_symbol_api'].upper()} Price History")
                    v_chart = generate_volume_chart(data["dates"], data["volumes"], f"{data['token_symbol_api'].upper()} Volume History")
                    console.print(p_chart)
                    console.print(v_chart)
                 return

            console.print(f"[bold green]Successfully exported report to {filepath}[/bold green]")
            
        except Exception as e:
            console.print(generate_error_panel(
                "Export Failed",
                f"Failed to save {output_mode.value} report to {filepath}.",
                [str(e), "Check file permissions", "Ensure directory exists"]
            ))

if __name__ == "__main__":
    main()
