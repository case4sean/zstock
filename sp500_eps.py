∏import yfinance as yf
import pandas as pd
import numpy as np
import argparse
from datetime import datetime
import requests
from io import StringIO
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import glob

# Parse command line arguments
parser = argparse.ArgumentParser(description='Scan S&P 500 stocks for EPS and valuation metrics')
parser.add_argument('--min-eps', type=float, help='Minimum EPS threshold (optional)')
parser.add_argument('--max-pe', type=float, help='Maximum P/E ratio threshold (optional)')
parser.add_argument('--min-growth', type=float, default=0, help='Minimum EPS growth percentage (default: 0)')
parser.add_argument('--threads', type=int, default=10, help='Number of concurrent threads to use (default: 10)')
parser.add_argument('--ticker-file', type=str, help='Path to text file containing ticker symbols (one per line)')
args = parser.parse_args()

min_eps = args.min_eps
max_pe = args.max_pe
min_growth = args.min_growth
num_threads = args.threads
ticker_file = args.ticker_file

def read_tickers_from_file(filepath):
    """Read ticker symbols from a text file (one ticker per line)."""
    try:
        with open(filepath, 'r') as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        return tickers
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        exit(1)
    except Exception as e:
        print(f"Error reading ticker file: {e}")
        exit(1)

def fetch_sp500_tickers():
    """Fetch S&P 500 ticker list from Wikipedia."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))

        # The first table contains the S&P 500 constituents
        sp500_table = tables[0]
        if 'Symbol' in sp500_table.columns:
            tickers = sp500_table['Symbol'].tolist()
            return tickers
        raise ValueError("Could not find S&P 500 constituents table")
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        exit(1)

def fetch_ticker_eps_data(symbol):
    """Fetch EPS and related metrics for a single ticker.

    Returns dict with: ticker, name, price, eps, forward_eps, pe_ratio,
                       forward_pe, eps_growth, market_cap, sector
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Extract basic info
        name = info.get('longName', 'N/A')
        sector = info.get('sector', 'N/A')
        price = info.get('currentPrice', info.get('regularMarketPrice', None))
        market_cap = info.get('marketCap', None)

        # Get EPS metrics
        eps = info.get('trailingEps', None)  # Trailing 12 months EPS
        forward_eps = info.get('forwardEps', None)  # Forward EPS estimate

        # Get P/E ratios
        pe_ratio = info.get('trailingPE', None)
        forward_pe = info.get('forwardPE', None)

        # Calculate EPS growth
        eps_growth = None
        if eps and forward_eps and eps > 0:
            eps_growth = ((forward_eps - eps) / abs(eps)) * 100

        # Get quarterly earnings growth
        quarterly_growth = info.get('earningsQuarterlyGrowth', None)
        if quarterly_growth is not None:
            quarterly_growth = quarterly_growth * 100

        return {
            'ticker': symbol,
            'name': name,
            'sector': sector,
            'price': price,
            'market_cap': market_cap,
            'eps': eps,
            'forward_eps': forward_eps,
            'pe_ratio': pe_ratio,
            'forward_pe': forward_pe,
            'eps_growth': eps_growth,
            'quarterly_growth': quarterly_growth
        }
    except Exception as e:
        return {
            'ticker': symbol,
            'name': 'N/A',
            'sector': 'N/A',
            'price': None,
            'market_cap': None,
            'eps': None,
            'forward_eps': None,
            'pe_ratio': None,
            'forward_pe': None,
            'eps_growth': None,
            'quarterly_growth': None
        }

def fetch_ticker_with_progress(symbol, completed_count, total, lock):
    """Wrapper for fetch_ticker_eps_data with thread-safe progress tracking."""
    data = fetch_ticker_eps_data(symbol)

    with lock:
        completed_count[0] += 1
        print(f"Progress: {completed_count[0]}/{total} - Fetched {symbol}")

    return data

# Fetch ticker list
if ticker_file:
    print(f"Reading tickers from file: {ticker_file}")
    tickers = read_tickers_from_file(ticker_file)
    ticker_source = "custom"
else:
    print("Fetching S&P 500 tickers from Wikipedia...")
    tickers = fetch_sp500_tickers()
    ticker_source = "sp500"

print(f"Found {len(tickers)} tickers")
print(f"Scanning with {num_threads} threads\n")

# Apply filters message
filters = []
if min_eps:
    filters.append(f"EPS >= {min_eps}")
if max_pe:
    filters.append(f"P/E <= {max_pe}")
if min_growth > 0:
    filters.append(f"EPS Growth >= {min_growth}%")

if filters:
    print(f"Filters: {' AND '.join(filters)}\n")

# Scan all tickers using thread pool
results = []
total = len(tickers)
completed_count = [0]
lock = Lock()

start_time = time.time()

with ThreadPoolExecutor(max_workers=num_threads) as executor:
    future_to_ticker = {
        executor.submit(fetch_ticker_with_progress, symbol, completed_count, total, lock): symbol
        for symbol in tickers
    }

    for future in as_completed(future_to_ticker):
        symbol = future_to_ticker[future]
        try:
            data = future.result()
            results.append(data)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            results.append({
                'ticker': symbol,
                'name': 'N/A',
                'sector': 'N/A',
                'price': None,
                'market_cap': None,
                'eps': None,
                'forward_eps': None,
                'pe_ratio': None,
                'forward_pe': None,
                'eps_growth': None,
                'quarterly_growth': None
            })

elapsed_time = time.time() - start_time
print(f"\nCompleted scanning {total} tickers in {elapsed_time:.1f} seconds")

# Filter results
filtered_results = []
incomplete_results = []

for data in results:
    # Check if data is complete
    if data['eps'] is None:
        incomplete_results.append(data)
        continue

    # Apply filters
    passes_filters = True

    if min_eps is not None and (data['eps'] is None or data['eps'] < min_eps):
        passes_filters = False

    if max_pe is not None and (data['pe_ratio'] is None or data['pe_ratio'] > max_pe):
        passes_filters = False

    if min_growth > 0:
        growth = data['eps_growth'] if data['eps_growth'] is not None else data['quarterly_growth']
        if growth is None or growth < min_growth:
            passes_filters = False

    if passes_filters:
        filtered_results.append(data)
    else:
        incomplete_results.append(data)

# Sort by EPS (descending - highest first)
filtered_results.sort(key=lambda x: x['eps'] if x['eps'] is not None else -999999, reverse=True)

print(f"\nFound {len(filtered_results)} tickers matching criteria")
print(f"{len(incomplete_results)} tickers excluded (incomplete data or filters)")

def format_value(value, decimals=2, prefix='', suffix=''):
    """Format numeric value or return N/A for None."""
    if value is None:
        return 'N/A'
    return f"{prefix}{value:.{decimals}f}{suffix}"

def format_market_cap(value):
    """Format market cap in billions or millions."""
    if value is None:
        return 'N/A'
    if value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif value >= 1e6:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value:.0f}"

def print_results_table(results, title):
    """Print results in formatted table."""
    if not results:
        print(f"\n{title}")
        print("No results to display")
        return

    print(f"\n{title}")
    print("=" * 140)
    header = f"{'Ticker':<8} {'EPS':<8} {'Fwd EPS':<8} {'EPS Grw%':<10} {'P/E':<8} {'Fwd P/E':<8} {'Price':<10} {'Mkt Cap':<10} {'Sector':<20}"
    print(header)
    print("-" * 140)

    for data in results[:50]:  # Show top 50
        ticker = data['ticker']
        eps = format_value(data['eps'], 2)
        forward_eps = format_value(data['forward_eps'], 2)
        eps_growth = format_value(data['eps_growth'], 1, suffix='%')
        pe = format_value(data['pe_ratio'], 1)
        fwd_pe = format_value(data['forward_pe'], 1)
        price = format_value(data['price'], 2, prefix='$')
        mkt_cap = format_market_cap(data['market_cap'])
        sector = data['sector'][:19] if len(data['sector']) > 19 else data['sector']

        print(f"{ticker:<8} {eps:<8} {forward_eps:<8} {eps_growth:<10} {pe:<8} {fwd_pe:<8} {price:<10} {mkt_cap:<10} {sector:<20}")

    if len(results) > 50:
        print(f"\n... and {len(results) - 50} more (see CSV file for complete results)")

# Print results
filter_desc = f" (Filtered)" if (min_eps or max_pe or min_growth > 0) else ""
print_results_table(filtered_results, f"Top S&P 500 Companies by EPS{filter_desc}")

def save_to_csv(filtered_results, incomplete_results, filename):
    """Save results to CSV file."""
    csv_data = []

    # Add filtered results
    for data in filtered_results:
        csv_data.append({
            'Ticker': data['ticker'],
            'Name': data['name'],
            'Sector': data['sector'],
            'Price': data['price'],
            'Market_Cap': data['market_cap'],
            'EPS': data['eps'],
            'Forward_EPS': data['forward_eps'],
            'EPS_Growth_%': data['eps_growth'],
            'Quarterly_Growth_%': data['quarterly_growth'],
            'PE_Ratio': data['pe_ratio'],
            'Forward_PE': data['forward_pe'],
            'Data_Status': 'Complete'
        })

    # Add incomplete results
    for data in incomplete_results:
        csv_data.append({
            'Ticker': data['ticker'],
            'Name': data['name'],
            'Sector': data['sector'],
            'Price': data['price'],
            'Market_Cap': data['market_cap'],
            'EPS': data['eps'],
            'Forward_EPS': data['forward_eps'],
            'EPS_Growth_%': data['eps_growth'],
            'Quarterly_Growth_%': data['quarterly_growth'],
            'PE_Ratio': data['pe_ratio'],
            'Forward_PE': data['forward_pe'],
            'Data_Status': 'Incomplete'
        })

    df = pd.DataFrame(csv_data)
    df.to_csv(filename, index=False)
    print(f"\nResults saved to: {filename}")

# Generate timestamped filename
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_filename = f"{ticker_source}_eps_{timestamp}.csv"

# Save to CSV
save_to_csv(filtered_results, incomplete_results, csv_filename)

print("\n=================:")
csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print(f"Average EPS: ${complete['EPS'].mean():.2f}")
print(f"Average Forward EPS: ${complete['Forward_EPS'].mean():.2f}")
print(f"Average P/E: {complete['PE_Ratio'].mean():.2f}x")
print(f"Average Forward P/E: {complete['Forward_PE'].mean():.2f}x")

print("\nTop 5 by EPS:")
print(complete.nlargest(5, 'EPS')[['Ticker', 'EPS', 'PE_Ratio']])
