# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a stock investment simulation tool that uses Dollar Cost Averaging (DCA) strategy with dividend reinvestment. The codebase analyzes the performance of regular investments in a specified ticker symbol over a date range, automatically reinvesting dividends.

## Running the Code

### Setup (First Time Only)

1. **Create a virtual environment:**
```bash
python3 -m venv venv
```

2. **Activate the virtual environment:**
```bash
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install yfinance pandas numpy lxml
```

Required dependencies:
- `yfinance` - Yahoo Finance API for stock data
- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing
- `lxml` - HTML/XML parsing (required for scan_nasdaq.py)

**Note:** After the initial setup, you only need to activate the virtual environment before running scripts:
```bash
source venv/bin/activate
```

### Running playtick.py

Run with default parameters (JEPQ, 2024-01-01 to 2025-01-01, $100/week):
```bash
source venv/bin/activate
python3 playtick.py
```

Run with custom parameters:
```bash
source venv/bin/activate
python3 playtick.py --ticker SPY --start 2024-01-01 --end 2024-12-31
python3 playtick.py --ticker JEPQ --weekly-investment 200 --buy-day 0
```

Available command-line options:
- `--ticker`: Stock ticker symbol (default: JEPQ)
- `--start`: Start date in YYYY-MM-DD format (default: 2024-01-01)
- `--end`: End date in YYYY-MM-DD format (default: 2025-01-01)
- `--buy-day`: Day of week to buy - 0=Monday, 1=Tuesday, 2=Wednesday, etc. (default: 2)
- `--weekly-investment`: Weekly investment amount in dollars (default: 100)

View all options:
```bash
python3 playtick.py --help
```

## Code Architecture

### Main Script: playtick.py

**Configuration Variables (lines 5-8):**
- `ticker`: Stock ticker symbol to analyze (e.g., 'JEPQ')
- `buy_day`: Day of week for regular purchases (0=Monday, 1=Tuesday, 2=Wednesday, etc.)
- `start_date` and `end_date`: Investment period range

**Core Logic Flow:**

1. **Data Acquisition (lines 21-27):**
   - Downloads historical price data using yfinance for the specified ticker and date range
   - Validates data was successfully downloaded and exits with error message if ticker is invalid

2. **Dividend Data Processing (lines 18-21):**
   - Fetches dividend payment dates and amounts
   - Normalizes timezone information for date matching

3. **Investment Date Calculation (lines 24-44):**
   - Generates all target investment days based on `buy_day` weekday
   - Handles non-trading days by rolling forward to the next available trading day
   - Prevents date range overflow with boundary checks

4. **Dividend Data Processing (lines 28-38):**
   - Handles both dividend-paying and non-dividend stocks
   - For dividend-paying stocks: normalizes timezone and filters to date range
   - For non-dividend stocks: creates empty dividend index to avoid errors

**Dividend Date Integration (lines 48-51):**
   - Merges dividend payment dates into the investment schedule
   - Ensures dividend dates are actual trading days
   - Skips this step if no dividends are available

5. **Investment Simulation (lines 57-68):**
   - Iterates through all investment dates in chronological order
   - On dividend dates: Reinvests dividends by purchasing additional shares (lines 59-61)
   - On regular investment dates: Purchases shares with fixed weekly investment amount (lines 63-68)
   - Tracks cumulative shares held and total cash invested

6. **Performance Calculation (lines 71-75):**
   - Computes final portfolio value using last closing price
   - Calculates total return percentage

### Key Implementation Details

**Trading Day Adjustment:** The script handles weekends and market holidays by searching forward for the next valid trading day (lines 37-44). This ensures investments always execute on actual market days.

**Dividend Reinvestment:** On dividend payment dates, the script calculates additional shares that can be purchased using the dividend amount (line 60). This compounds returns over time without additional cash investment.

**Data Structure:** Uses pandas DataFrame indexed by date for efficient date-based lookups and iteration. The `investment_days` list maintains chronological order for the simulation.

### S&P 500 EPS Scanner: sp500_eps.py

**Purpose:** Scans S&P 500 stocks to analyze EPS (Earnings Per Share), EPS growth, and valuation metrics.

**Usage:**

Scan all S&P 500 stocks (fetched from Wikipedia):
```bash
source venv/bin/activate
python3 sp500_eps.py
```

Scan with filters for value stocks:
```bash
source venv/bin/activate
python3 sp500_eps.py --min-eps 5 --max-pe 20 --min-growth 15
```

Scan custom ticker list:
```bash
source venv/bin/activate
python3 sp500_eps.py --ticker-file tickers.txt
```

Fast scan with more threads:
```bash
source venv/bin/activate
python3 sp500_eps.py --threads 20 --min-eps 10
```

View options:
```bash
python3 sp500_eps.py --help
```

**Command-line options:**
- `--min-eps`: Minimum EPS threshold (e.g., 5.0)
- `--max-pe`: Maximum P/E ratio threshold (e.g., 20.0)
- `--min-growth`: Minimum EPS growth percentage (default: 0)
- `--threads`: Number of concurrent threads (default: 10)
- `--ticker-file`: Path to custom ticker list file

**Output:**
- Console: Formatted table showing top 50 companies sorted by EPS
- CSV: Timestamped file `sp500_eps_YYYY-MM-DD_HH-MM.csv` with complete results

**Metrics Displayed:**
- EPS: Trailing 12-month Earnings Per Share
- Fwd EPS: Forward EPS estimate
- EPS Grw%: Year-over-year EPS growth percentage
- P/E: Current Price-to-Earnings ratio
- Fwd P/E: Forward P/E ratio
- Price: Current stock price
- Mkt Cap: Market capitalization
- Sector: Company sector

**Example Filters:**

Find undervalued growth stocks:
```bash
python3 sp500_eps.py --min-eps 5 --max-pe 15 --min-growth 20
```

Find high EPS companies:
```bash
python3 sp500_eps.py --min-eps 10 --threads 20
```

**Analyzing Results (Calculate Statistics):**

After running a scan, you can calculate statistics from the CSV file:

```bash
source venv/bin/activate

# Calculate average EPS, Forward EPS, and P/E ratios
python3 << 'EOF'
import pandas as pd
import glob

# Find most recent scan
csv_files = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)
df = pd.read_csv(csv_files[0])
complete_df = df[df['Data_Status'] == 'Complete']

# Calculate averages
print(f"Average EPS: ${complete_df['EPS'].mean():.2f}")
print(f"Average Forward EPS: ${complete_df['Forward_EPS'].mean():.2f}")
print(f"Average P/E Ratio: {complete_df['PE_Ratio'].mean():.2f}x")
print(f"Average Forward P/E: {complete_df['Forward_PE'].mean():.2f}x")
print(f"\nMedian EPS: ${complete_df['EPS'].median():.2f}")
print(f"Median P/E Ratio: {complete_df['PE_Ratio'].median():.2f}x")

# By sector
print("\nAverage EPS by Sector:")
print(complete_df.groupby('Sector')['EPS'].mean().sort_values(ascending=False).round(2))
EOF
```

**Example Output:**
```
Average EPS: $9.13
Average Forward EPS: $13.49
Average P/E Ratio: 38.91x
Average Forward P/E: 18.09x

Median EPS: $4.86
Median P/E Ratio: 27.21x

Average EPS by Sector:
Consumer Cyclical       25.04
Financial Services      11.69
Industrials              9.31
Healthcare               8.08
...
```

**Notes:**
- Fetches S&P 500 list automatically from Wikipedia
- Multi-threaded processing: S&P 500 scan (~500 tickers) completes in ~30-60 seconds with 20 threads
- Results sorted by EPS (highest first)
- Shows top 50 in console, all results saved to CSV
- Filters are applied with AND logic (all conditions must be met)
- Use Python pandas to analyze CSV files for custom statistics

---

### Stock Scanner: scan_nasdaq.py

**Purpose:** Scans stocks to find tickers with P/FCF (Price-to-Free Cash Flow) ratio below a specified threshold.

**Usage:**

Scan Nasdaq 100 (fetched from Wikipedia):
```bash
source venv/bin/activate
python3 scan_nasdaq.py
```

Scan custom ticker list from file:
```bash
source venv/bin/activate
python3 scan_nasdaq.py --ticker-file tickers.txt
```

Scan with custom P/FCF threshold:
```bash
source venv/bin/activate
python3 scan_nasdaq.py --max-pfcf 10
python3 scan_nasdaq.py --ticker-file tickers.txt --max-pfcf 10
```

Scan with custom thread count (faster):
```bash
source venv/bin/activate
python3 scan_nasdaq.py --threads 20  # Use 20 concurrent threads
python3 scan_nasdaq.py --ticker-file tickers.txt --threads 15 --max-pfcf 10
```

View options:
```bash
python3 scan_nasdaq.py --help
```

**Command-line options:**
- `--max-pfcf`: Maximum P/FCF ratio threshold (default: 15.0)
- `--ticker-file`: Path to text file containing ticker symbols (one per line)
- `--threads`: Number of concurrent threads for faster processing (default: 10)

**Ticker File Format:**
Create a text file with one ticker symbol per line:
```
AAPL
MSFT
GOOGL
TSLA
```

Example file provided: `tickers.txt`

**Output:**
- Console: Formatted table showing filtered tickers with metrics
- CSV: Timestamped file `nasdaq_scan_YYYY-MM-DD_HH-MM.csv` (from Wikipedia) or `custom_scan_YYYY-MM-DD_HH-MM.csv` (from file)

**Metrics Displayed:**
- P/FCF: Price-to-Free Cash Flow ratio
- P/E: Price-to-Earnings ratio (trailing or forward)
- Growth%: Earnings or revenue growth percentage
- EV/Sales: Enterprise Value to Sales ratio
- Price: Current stock price
- Name: Company name

**Analyzing Results (Calculate Statistics):**

After running a scan, analyze the results from CSV:

```bash
source venv/bin/activate

# Calculate average P/FCF and other metrics
python3 << 'EOF'
import pandas as pd
import glob

# Find most recent scan
csv_files = sorted(glob.glob('nasdaq_scan_*.csv'), reverse=True)
df = pd.read_csv(csv_files[0])
complete_df = df[df['Data_Status'] == 'Complete']

# Calculate averages
print(f"Average P/FCF: {complete_df['P/FCF'].mean():.2f}x")
print(f"Average P/E: {complete_df['P/E'].mean():.2f}x")
print(f"Average Growth: {complete_df['Growth%'].mean():.1f}%")
print(f"Average EV/Sales: {complete_df['EV/Sales'].mean():.2f}x")

print(f"\nMedian P/FCF: {complete_df['P/FCF'].median():.2f}x")
print(f"Median P/E: {complete_df['P/E'].median():.2f}x")

# Top 10 best P/FCF
print("\nTop 10 Best P/FCF Ratios:")
print(complete_df.nsmallest(10, 'P/FCF')[['Ticker', 'P/FCF', 'P/E', 'Growth%']])
EOF
```

**Notes:**
- By default, fetches Nasdaq 100 list automatically from Wikipedia
- Use `--ticker-file` to scan custom ticker lists
- **Multi-threaded processing:** Uses concurrent threads for fast scanning (default: 10 threads)
  - Nasdaq 100 scan: ~15-30 seconds with 10 threads vs. ~4 minutes sequential
  - Increase threads with `--threads` for faster scanning (recommended: 10-20 threads)
- Handles missing/incomplete data separately
- Results sorted by P/FCF (best values first)
- Only shows tickers with P/FCF below threshold AND growth > 10%
- Use Python pandas to analyze CSV files for custom statistics

## Analyzing CSV Results

After running any scanner, you can analyze the generated CSV files using Python:

### Quick Statistics Commands

**For S&P 500 EPS scans:**
```bash
source venv/bin/activate
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print(f"📊 S&P 500 Statistics from: {csv}\n")
print(f"Total tickers: {len(df)}")
print(f"Complete data: {len(complete)}\n")

print("💰 EPS Metrics:")
print(f"  Average EPS: ${complete['EPS'].mean():.2f}")
print(f"  Average Forward EPS: ${complete['Forward_EPS'].mean():.2f}")
print(f"  Median EPS: ${complete['EPS'].median():.2f}\n")

print("📈 Valuation Metrics:")
print(f"  Average P/E: {complete['PE_Ratio'].mean():.2f}x")
print(f"  Average Forward P/E: {complete['Forward_PE'].mean():.2f}x")
print(f"  Median P/E: {complete['PE_Ratio'].median():.2f}x\n")

print("🏆 Top 5 by EPS:")
print(complete.nlargest(5, 'EPS')[['Ticker', 'Name', 'EPS', 'PE_Ratio']])

print("\n📊 By Sector:")
print(complete.groupby('Sector')['EPS'].agg(['mean', 'count']).round(2).sort_values('mean', ascending=False))
EOF
```

**For Nasdaq P/FCF scans:**
```bash
source venv/bin/activate
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('nasdaq_scan_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print(f"📊 Nasdaq Scan Statistics from: {csv}\n")
print(f"Total tickers: {len(df)}")
print(f"Complete data: {len(complete)}\n")

print("💰 Value Metrics:")
print(f"  Average P/FCF: {complete['P/FCF'].mean():.2f}x")
print(f"  Median P/FCF: {complete['P/FCF'].median():.2f}x")
print(f"  Average P/E: {complete['P/E'].mean():.2f}x")
print(f"  Average Growth: {complete['Growth%'].mean():.1f}%\n")

print("🏆 Top 10 Best P/FCF:")
top = complete.nsmallest(10, 'P/FCF')[['Ticker', 'P/FCF', 'P/E', 'Growth%', 'Price']]
print(top.to_string(index=False))
EOF
```

**Compare multiple scans:**
```bash
# Compare today's scan vs yesterday's
python3 << 'EOF'
import pandas as pd
import glob

files = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[:2]
df1 = pd.read_csv(files[0])
df2 = pd.read_csv(files[1]) if len(files) > 1 else None

print(f"Latest scan: {files[0]}")
print(f"Average EPS: ${df1[df1['Data_Status']=='Complete']['EPS'].mean():.2f}")

if df2 is not None:
    print(f"\nPrevious scan: {files[1]}")
    print(f"Average EPS: ${df2[df2['Data_Status']=='Complete']['EPS'].mean():.2f}")
EOF
```

### Custom Analysis Examples

**Find stocks with specific criteria:**
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('sp500_eps_2026-02-28_13-11.csv')

# High EPS growth with reasonable P/E
filtered = df[(df['EPS_Growth_%'] > 20) & (df['PE_Ratio'] < 25) & (df['EPS'] > 5)]
print(f"Found {len(filtered)} stocks with >20% growth, P/E < 25, EPS > $5")
print(filtered[['Ticker', 'EPS', 'EPS_Growth_%', 'PE_Ratio']].sort_values('EPS', ascending=False))
EOF
```

**Sector comparison:**
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('sp500_eps_2026-02-28_13-11.csv')

sector_stats = df.groupby('Sector').agg({
    'EPS': ['mean', 'median'],
    'PE_Ratio': ['mean', 'median'],
    'Ticker': 'count'
}).round(2)
sector_stats.columns = ['Avg_EPS', 'Med_EPS', 'Avg_PE', 'Med_PE', 'Count']
print(sector_stats.sort_values('Avg_EPS', ascending=False))
EOF
```

---

## Modifying the Simulation

To test different scenarios, use command-line arguments:
- `--ticker`: Analyze different stocks or ETFs
- `--buy-day`: Test different purchase day strategies (0=Monday through 6=Sunday)
- `--weekly-investment`: Simulate different investment amounts
- `--start` and `--end`: Analyze different time periods

Alternatively, you can modify the default values in playtick.py (lines 8-12) for the argparse configuration.

### Testing Different Stock Types

The script handles both dividend-paying and non-dividend stocks:

**Dividend-paying stocks:**
```bash
source venv/bin/activate
python3 playtick.py --ticker JEPQ    # High dividend ETF
python3 playtick.py --ticker AAPL    # Tech stock with dividends
python3 playtick.py --ticker SPY     # S&P 500 ETF with dividends
```

**Non-dividend stocks:**
```bash
source venv/bin/activate
python3 playtick.py --ticker TSLA    # Growth stock, no dividends
python3 playtick.py --ticker BRK-B   # Berkshire Hathaway, no dividends
```

Note: Use hyphens instead of dots in ticker symbols (e.g., BRK-B not BRK.B)
