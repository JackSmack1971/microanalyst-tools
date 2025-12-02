# Microanalyst Tools CLI

A professional-grade cryptocurrency analysis CLI tool for terminal-based market research.

## Features

- **Real-time Data**: Fetches price, volume, and order book data from CoinGecko and Binance.
- **Command Center Dashboard**: Full-screen, single-view terminal dashboard with dynamic layouts.
- **Multi-Token Comparison**: Compare up to 10 tokens side-by-side with correlation heatmaps.
- **Instant-Recall Caching**: Smart disk-based caching to speed up repeated queries and reduce API usage.
- **Visualizations**: ASCII price and volume charts directly in the terminal.
- **Export Options**: Save reports as JSON or HTML.
- **Configurable**: YAML-based configuration for defaults and thresholds.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Analysis
Analyze a single token:
```bash
python -m microanalyst btc
```

### Interactive Mode
Search and select tokens interactively:
```bash
python -m microanalyst -i
```

### Enhanced CLI Features

#### Comparison Mode & Correlation Heatmap
Compare multiple tokens (2-10) to spot opportunities and view a Pearson correlation heatmap:
```bash
python -m microanalyst --compare btc,eth,sol
```

#### Caching
Data is automatically cached to disk (TTL: 5 min for market data, 1 min for prices). Cached data is indicated by a `(Cached)` label. No configuration required.

#### Visualizations
Display price and volume charts:
```bash
python -m microanalyst btc --charts
```
Combine with comparison for multi-token charts:
```bash
python -m microanalyst --compare btc,eth --charts
```

#### Exporting Reports
Save analysis to a file:
```bash
python -m microanalyst btc --output json --save report.json
python -m microanalyst btc --output html
```

#### Configuration
Load a custom configuration file:
```bash
python -m microanalyst btc --config my_config.yaml
```

**Example `config.yaml`:**
```yaml
defaults:
  days: 30
  output_format: "terminal"

thresholds:
  volatility:
    high: 0.05
    medium: 0.02
  liquidity:
    min_depth_usd: 50000
```

#### Accessibility
Disable colored output for CI/CD or logging:
```bash
python -m microanalyst btc --no-color
```
Or use the environment variable:
```bash
export NO_COLOR=1
python -m microanalyst btc
```

## Troubleshooting

- **API Rate Limits**: If you see errors related to CoinGecko, wait a minute and try again.
- **Missing Data**: Some low-cap tokens may not have Binance data.
