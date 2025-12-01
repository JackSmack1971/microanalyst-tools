import sys
import argparse
import logging
from rich.console import Console
from rich.markdown import Markdown
from rich.logging import RichHandler
from rich.traceback import install
from src.cli.theme import generate_error_panel
from src.cli.progress import create_progress_bar, STAGE_DESCRIPTIONS

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

def main():
    parser = argparse.ArgumentParser(description="Elite Cryptocurrency Microanalyst Tool")
    parser.add_argument("token", help="Token symbol (e.g., btc, eth, sol)")
    parser.add_argument("--days", default="30", help="Days of historical data (default: 30)")
    args = parser.parse_args()

    token_symbol = args.token.lower()
    
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

        # 1. Fetch Data
        # Quick search to get ID
        search_results = cg_client._request("search", params={"query": token_symbol})
        if not search_results or not search_results.get("coins"):
            progress.stop()
            console.print(generate_error_panel(
                "Token Not Found",
                f"Token '{token_symbol}' not found on CoinGecko.",
                ["Check spelling", "Try using the full name", "Verify token exists on CoinGecko"]
            ))
            return
        
        # Pick the first exact match or the first result
        token_id = search_results["coins"][0]["id"]
        token_symbol_api = search_results["coins"][0]["symbol"] # e.g., 'btc'
        logger.info(f"Resolved {token_symbol} to CoinGecko ID: {token_id}, Symbol: {token_symbol_api}")
        progress.update(task_search, advance=1)

        cg_data = cg_client.get_token_data(token_id)
        market_chart = cg_client.get_market_chart(token_id, days=args.days)
        
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
    
    # 3. Report
    report_md = generate_report(
        token_symbol,
        cg_data,
        ticker_24h,
        volatility_metrics,
        volume_metrics,
        liquidity_metrics,
        validation_flags={}
    )
    
    console.print(Markdown(report_md))

if __name__ == "__main__":
    main()
