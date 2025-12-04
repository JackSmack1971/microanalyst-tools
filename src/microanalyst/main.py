import sys
import os
import argparse
import logging
from typing import Dict, Any, List, Optional
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
    calculate_liquidity_metrics,
    calculate_technical_indicators
)
from src.comparison.comparator import compare_tokens
from src.comparison.comparator import compare_tokens
from rich.layout import Layout
from rich.live import Live
import time
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
from rich import box
from src.microanalyst.reporting.generator import (
    generate_report, 
    generate_comparison_table, 
    generate_correlation_table,
    generate_overview_panel,
    generate_metric_table,
    generate_risk_table
)
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

from src.microanalyst.services.analyzer import TokenAnalyzer

def analyze_token(token_symbol: str, cg_client: CoinGeckoClient, binance_client: BinanceClient, days: int, progress=None, task_ids=None, btc_volatility: Optional[float] = None) -> Dict[str, Any]:
    """
    Analyzes a single token and returns all relevant data and metrics.
    Wraps TokenAnalyzer to maintain CLI compatibility.
    """
    analyzer = TokenAnalyzer(cg_client, binance_client)
    
    def progress_callback(step: str, description: Optional[str]):
        if progress and task_ids:
            task_id = task_ids.get(step)
            if task_id is not None:
                if description:
                    progress.update(task_id, description=description)
                else:
                    progress.update(task_id, advance=1)

    return analyzer.analyze(token_symbol, days, btc_volatility, progress_callback)

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
    parser.add_argument("--watch", action="store_true", help="Enable live market monitor mode")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()

    # Handle No Color Mode
    if args.no_color or os.environ.get("NO_COLOR"):
        console.no_color = True
        # Also disable plotext color if possible, though theme('clear') is mostly monochrome.
        # We can force it if needed, but console.no_color handles Rich output.

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

    # Fetch BTC Baseline for Benchmarking
    btc_volatility = None
    try:
        if not args.compare: # Only needed for single token analysis primarily, but good for compare too?
             # Let's fetch it always, it's cached usually.
             console.print("[dim]Fetching Bitcoin baseline...[/dim]")
             btc_chart = cg_client.get_market_chart("bitcoin", days=days)
             if btc_chart and btc_chart.get("prices"):
                 btc_prices = [p[1] for p in btc_chart["prices"]]
                 btc_metrics = calculate_volatility_metrics(btc_prices)
                 btc_volatility = btc_metrics.get("cv")
    except Exception as e:
        logger.warning(f"Failed to fetch BTC baseline: {e}")

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
                data = analyze_token(token, cg_client, binance_client, days, progress, task_ids, btc_volatility)
                if data:
                    data["symbol"] = data["token_symbol_api"].upper()
                    results.append(data)
                else:
                    console.print(f"[yellow]Skipping {token} (failed to analyze)[/yellow]")
                    
        if len(results) < 2:
            console.print(generate_error_panel("Comparison Failed", "Not enough valid tokens to compare.", []))
            return
            
        # Compare
        metrics_df, correlation_df = compare_tokens(results)
        
        # Render Comparison Table
        comp_table = generate_comparison_table(metrics_df)
        console.print(comp_table)
        
        # Render Correlation Heatmap
        if not correlation_df.empty:
            console.print("\n")
            corr_table = generate_correlation_table(correlation_df)
            console.print(corr_table)
        
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
    # Frictionless Entry: If no token/compare args and TTY, default to interactive
    if not args.token and not args.compare and sys.stdout.isatty():
        args.interactive = True

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
            parser.print_help()
            return

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
        
        data = analyze_token(resolved_token_symbol, cg_client, binance_client, days, progress, task_ids, btc_volatility)
        
    if not data:
        console.print(generate_error_panel(
            "Analysis Failed",
            f"Could not analyze token '{resolved_token_symbol}'.",
            ["Check token symbol", "Verify network connection", "Try again later"]
        ))
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
        "imbalance": data["imbalance"],
        "rsi": data["ta_metrics"].get("rsi"),
        "trend": data["ta_metrics"].get("trend"),
        "beta": data.get("beta_proxy")
    }
    
    metric_labels = {
        "volatility": "Volatility (CV)",
        "spread": "Spread",
        "volume_delta": "Volume Delta",
        "imbalance": "Imbalance",
        "rsi": "RSI (14D)",
        "trend": "Trend (20/50)",
        "beta": "Beta (vs BTC)"
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
            elif key == "rsi": fmt_val = format_number(val, 1)
            elif key == "trend": fmt_val = str(val)
            elif key == "beta": fmt_val = format_number(val, 2)

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
        # Create Layout
        # Create Layout (handled by generate_report now)
        # layout = Layout() ...

        def update_dashboard(data, timestamp, status_msg=None):
            # Prepare charts if enabled
            charts = None
            if args.charts:
                chart_height = max(15, (console.size.height - 10) // 2)
                chart_width = console.size.width - 6
                
                p_chart = generate_price_chart(
                    data["dates"], 
                    data["prices"], 
                    f"{data['token_symbol_api'].upper()} Price History",
                    width=chart_width,
                    height=chart_height
                )
                charts = [Text.from_ansi(p_chart)]
                
                # Volume chart? The layout only has space for one chart easily in the current grid unless we stack them.
                # The original code stacked them.
                # Let's stack them in the charts list.
                # v_chart = generate_volume_chart(...)
                # For now, let's just stick to price chart as primary, or stack both.
                # The generate_report logic stacks all items in `charts` list into a Group.
                # So we can add volume chart too.
                # But let's keep it simple for now to match the "Glass Cockpit" request which mentioned "ASCII Charts".
                
            # Generate the Layout
            layout = generate_report(
                data["token_symbol"],
                data["cg_data"],
                data["ticker_24h"],
                data["volatility_metrics"],
                data["volume_metrics"],
                data["liquidity_metrics"],
                validation_flags={},
                config=config,
                charts=charts,
                ta_metrics=data["ta_metrics"],
                beta_proxy=data.get("beta_proxy"),
                risk_metrics=data.get("risk_metrics"),
                advanced_ta=data.get("advanced_ta")
            )
            
            # If status_msg, we might want to append it to the header?
            # generate_report creates the header.
            # We can update the header panel in the layout if needed.
            if status_msg:
                # Access the header renderable. It's a Panel wrapping Text.
                # It's easier to just pass status_msg to generate_report if we wanted, 
                # but we didn't add that arg.
                # We can hack it:
                current_header = layout["header"].renderable
                # But we can't easily modify the text inside the panel without reconstructing it.
                # Let's just leave it for now or update it if we really need to show [LIVE].
                # Actually, let's just update the header layout directly here.
                header_text = f"MICROANALYST REPORT: {data['token_symbol_api'].upper()} | {timestamp} | {status_msg}"
                layout["header"].update(Panel(Text(header_text, justify="center", style="bold white"), style="bold white on blue", box=box.HEAVY))

            return layout

        # Initial Render
        # Initial Render
        initial_layout = update_dashboard(data, timestamp)
        
        if args.watch:
            refresh_interval = config["defaults"].get("refresh_interval", 60)
            
            # Callback for rate limits
            def on_status(msg):
                pass

            cg_client.status_callback = on_status

            with Live(initial_layout, console=console, screen=True, refresh_per_second=4) as live:
                while True:
                    try:
                        time.sleep(refresh_interval)
                        
                        # Re-fetch data
                        new_data = analyze_token(resolved_token_symbol, cg_client, binance_client, days, progress=None, task_ids=None, btc_volatility=btc_volatility)
                        
                        if new_data:
                            new_timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                            new_layout = update_dashboard(new_data, new_timestamp, status_msg="[LIVE]")
                            live.update(new_layout)
                        else:
                            # Keep old data
                            pass
                            
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        logger.error(f"Watch loop error: {e}")
                        time.sleep(5) # Wait a bit before retry
        else:
            console.print(initial_layout)
        
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
                 charts = None
                 if args.charts:
                    console.print("\n[bold cyan]Generating Charts...[/bold cyan]")
                    p_chart = generate_price_chart(data["dates"], data["prices"], f"{data['token_symbol_api'].upper()} Price History")
                    v_chart = generate_volume_chart(data["dates"], data["volumes"], f"{data['token_symbol_api'].upper()} Volume History")
                    charts = [Text.from_ansi(p_chart), Text.from_ansi(v_chart)]

                 report_renderable = generate_report(
                    data["token_symbol"],
                    data["cg_data"],
                    data["ticker_24h"],
                    data["volatility_metrics"],
                    data["volume_metrics"],
                    data["liquidity_metrics"],
                    validation_flags={},
                    config=config,
                    charts=charts,
                    ta_metrics=data["ta_metrics"],
                    beta_proxy=data.get("beta_proxy"),
                    risk_metrics=data.get("risk_metrics"),
                    advanced_ta=data.get("advanced_ta")
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
