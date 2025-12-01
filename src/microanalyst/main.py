import sys
import argparse
import logging
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
from src.microanalyst.reporting.generator import generate_report

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

def main():
    # Load configuration early to use for defaults
    # We need to parse --config separately or just load defaults first then override?
    # Argparse doesn't easily support "load config then parse other args using config defaults" 
    # without two-pass parsing or manual handling.
    # Simpler approach: Parse args, load config (using --config if present), 
    # then if args are default/None, use config values.
    
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
    args = parser.parse_args()

    # Load Config
    try:
        config_path = Path(args.config) if args.config else None
        config = load_config(config_path)
        console.print(f"[dim]Loaded configuration from {config_path or 'defaults'}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load config: {e}. Using internal defaults.[/yellow]")
        config = load_config() # Fallback to internal defaults only

    # Apply defaults from config if args not provided
    days = int(args.days) if args.days else config["defaults"]["days"]
    output_mode_str = args.output if args.output else config["defaults"]["output_format"]
    output_mode = OutputMode(output_mode_str)

    # Determine mode
    is_interactive = args.interactive and sys.stdout.isatty()
    
    # Input handling
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

    # Initialize Clients
    cg_client = CoinGeckoClient()
    binance_client = BinanceClient()

    with create_progress_bar() as progress:
        # Define Tasks
        task_search = progress.add_task(STAGE_DESCRIPTIONS["token_search"], total=1)
        task_market = progress.add_task(STAGE_DESCRIPTIONS["market_data"], total=1)
        task_orderbook = progress.add_task(STAGE_DESCRIPTIONS["orderbook"], total=1)
        task_analysis = progress.add_task(STAGE_DESCRIPTIONS["analysis"], total=1)

        # Search
        try:
            search_results = cg_client.search(token_symbol)
        except Exception as e:
            progress.stop()
            console.print(generate_error_panel("Search Failed", f"Could not find token '{token_symbol}'", [str(e)]))
            return
        
        if not search_results or not search_results.get("coins"):
            progress.stop()
            console.print(generate_error_panel(
                "Token Not Found",
                f"Token '{token_symbol}' not found on CoinGecko.",
                ["Check spelling", "Try using the full name", "Verify token exists on CoinGecko"]
            ))
            return
        
        # Pick the first exact match or the first result
        if is_interactive:
            # Prompt user to select from search results
            selected_id = prompt_token_selection(search_results["coins"])
            if not selected_id:
                progress.stop()
                console.print("[yellow]Selection cancelled.[/yellow]")
                return
            
            # Find the selected coin object to get symbol
            selected_coin = next((c for c in search_results["coins"] if c["id"] == selected_id), None)
            token_id = selected_id
            token_symbol_api = selected_coin["symbol"] if selected_coin else token_symbol
            
        else:
            # Default behavior: pick first
            token_id = search_results["coins"][0]["id"]
            token_symbol_api = search_results["coins"][0]["symbol"] # e.g., 'btc'
            
        logger.info(f"Resolved {token_symbol} to CoinGecko ID: {token_id}, Symbol: {token_symbol_api}")
        progress.update(task_search, advance=1)

        # Fetch Market Data
        try:
            cg_data = cg_client.get_token_data(token_id)
            market_chart = cg_client.get_market_chart(token_id, days=days)
        except Exception as e:
            progress.stop()
            console.print(generate_error_panel("Data Fetch Error", "Failed to retrieve market data", [str(e)]))
            return
        
        if not cg_data or not market_chart:
            progress.stop()
            console.print(generate_error_panel(
                "Data Fetch Failed",
                "Failed to fetch CoinGecko data.",
                ["Check internet connection", "API might be down", "Rate limit exceeded"]
            ))
            return
        progress.update(task_market, advance=1)

        # Binance uses symbols like BTCUSDT
        binance_symbol = f"{token_symbol_api.upper()}USDT"
        logger.info(f"Using Binance Symbol: {binance_symbol}")
        ticker_24h = binance_client.get_ticker_24h(binance_symbol)
        depth = binance_client.get_depth(binance_symbol)
        
        if not ticker_24h:
            logger.warning(f"Could not fetch Binance data for {binance_symbol}. Some metrics will be missing.")
            ticker_24h = {}
            depth = {"bids": [], "asks": []}
        progress.update(task_orderbook, advance=1)

        # 2. Analyze
        # Extract prices/volumes from market chart
        # market_chart['prices'] is list of [timestamp, price]
        prices = [p[1] for p in market_chart.get("prices", [])]
        volumes = [v[1] for v in market_chart.get("total_volumes", [])]
        
        volatility_metrics = calculate_volatility_metrics(prices)
        volume_metrics = calculate_volume_metrics(prices, volumes)
        liquidity_metrics = calculate_liquidity_metrics(depth)
        progress.update(task_analysis, advance=1)
    
    # 3. Report / Export
    
    # Prepare common data structure for exports
    # Note: This duplicates some logic from generator.py, ideally we'd refactor generator to expose data prep.
    # For now, we build it here to satisfy the export interfaces.
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Calculate derived values for export
    cg_vol = cg_data.get("market_data", {}).get("total_volume", {}).get("usd", 0)
    bin_vol = float(ticker_24h.get("quoteVolume", 0))
    vol_delta = ((abs(cg_vol - bin_vol)) / cg_vol * 100) if cg_vol else 0.0
    
    report_data = {
        "token_symbol": token_symbol,
        "timestamp": timestamp,
        "overview": {
            "name": cg_data.get("name", "Unknown"),
            "symbol": cg_data.get("symbol", "???"),
            "rank": cg_data.get("market_cap_rank"),
            "price": format_currency(cg_data.get("market_data", {}).get("current_price", {}).get("usd")),
            "market_cap": format_currency(cg_data.get("market_data", {}).get("market_cap", {}).get("usd")),
            "volume_24h": format_currency(cg_vol)
        },
        "metrics": [],
        "risks": [],
        "confidence_score": 100
    }
    
    # Populate metrics list with signals
    raw_metrics = {
        "volatility": volatility_metrics.get("cv"),
        "spread": liquidity_metrics.get("spread_pct"),
        "volume_delta": vol_delta,
        "imbalance": liquidity_metrics.get("imbalance")
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
            
            # Format value
            fmt_val = str(val)
            if key == "volatility": fmt_val = format_number(val, 2)
            elif key == "spread": fmt_val = format_percentage(val / 100.0, 2) # spread is pct points
            elif key == "volume_delta": fmt_val = format_percentage(val / 100.0, 1) # delta is pct points
            elif key == "imbalance": fmt_val = format_number(val, 2)

            report_data["metrics"].append({
                "name": metric_labels.get(key, key),
                "value": fmt_val,
                "signal": signal,
                "signal_class": signal_class
            })

    # Populate risks (simplified logic matching generator.py)
    spread_val = raw_metrics["spread"] or 0.0
    imbalance_val = raw_metrics["imbalance"] or 1.0
    
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
            token_symbol,
            cg_data,
            ticker_24h,
            volatility_metrics,
            volume_metrics,
            liquidity_metrics,
            validation_flags={},
            config=config # Pass config
        )
        console.print(report_renderable)
        
    else:
        # Determine filepath
        if args.save:
            filepath = Path(args.save)
        else:
            date_str = datetime.utcnow().strftime("%Y%m%d")
            ext = "json" if output_mode == OutputMode.JSON else "html"
            filepath = Path(f"{token_symbol}_{date_str}.{ext}")
            
        try:
            if output_mode == OutputMode.JSON:
                export_to_json(report_data, filepath)
            elif output_mode == OutputMode.HTML:
                export_to_html(report_data, filepath)
            elif output_mode == OutputMode.MARKDOWN:
                 # Placeholder for markdown export if needed, or just warn
                 console.print("[yellow]Markdown export not yet implemented as file. Printing to terminal.[/yellow]")
                 report_renderable = generate_report(
                    token_symbol,
                    cg_data,
                    ticker_24h,
                    volatility_metrics,
                    volume_metrics,
                    liquidity_metrics,
                    validation_flags={},
                    config=config
                )
                 console.print(report_renderable)
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
