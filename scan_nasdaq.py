import yfinance as yf
import pandas as pd
import numpy as np
import argparse
from datetime import datetime
import requests
from io import StringIO
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Scan stocks for P/FCF ratio below threshold')
parser.add_argument('--max-pfcf', type=float, default=15.0, help='Maximum P/FCF ratio threshold (default: 15.0)')
parser.add_argument('--ticker-file', type=str, help='Path to text file containing ticker symbols (one per line)')
parser.add_argument('--threads', type=int, default=10, help='Number of concurrent threads to use (default: 10)')
args = parser.parse_args()

max_pfcf_threshold = args.max_pfcf
ticker_file = args.ticker_file
num_threads = args.threads

# Constants
MIN_GROWTH_THRESHOLD = 10.0  # Minimum growth percentage for filtering

def read_tickers_from_file(filepath):
    """Read ticker symbols from a text file (one ticker per line).

    Args:
        filepath: Path to text file containing tickers

    Returns:
        List of ticker symbols (whitespace stripped, empty lines ignored)
    """
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

def create_ticker_data_dict(ticker, name='N/A', price=None, p_fcf=None, p_e=None, growth=None, ev_sales=None):
    """Factory function for consistent ticker data dictionary structure."""
    return {
        'ticker': ticker,
        'name': name,
        'price': price,
        'p_fcf': p_fcf,
        'p_e': p_e,
        'growth': growth,
        'ev_sales': ev_sales
    }

def fetch_nasdaq100_tickers():
    """Fetch Nasdaq 100 ticker list from Wikipedia."""
    try:
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        # url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # Use requests to fetch HTML with User-Agent header
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))
        # The constituents table is typically the 4th table (index 3)
        # It has columns including 'Ticker'
        for table in tables:
            if 'Ticker' in table.columns:
                tickers = table['Ticker'].tolist()
            # if 'Symbol' in table.columns:
            #     tickers = table['Symbol'].tolist()
                return tickers
        raise ValueError("Could not find Nasdaq 100 constituents table")
    except Exception as e:
        print(f"Error fetching Nasdaq 100 tickers: {e}")
        exit(1)

def fetch_ticker_data(symbol):
    """Fetch financial metrics for a single ticker.

    Returns dict with: ticker, name, price, p_fcf, p_e, growth, ev_sales
    Returns None values for missing data.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Extract basic info
        name = info.get('longName', 'N/A')
        price = info.get('currentPrice', info.get('regularMarketPrice', None))

        # Calculate P/FCF
        market_cap = info.get('marketCap')
        free_cashflow = info.get('freeCashflow')
        p_fcf = None
        if market_cap and free_cashflow and free_cashflow > 0:
            p_fcf = market_cap / free_cashflow

        # Get P/E
        p_e = info.get('trailingPE', info.get('forwardPE', None))

        # Get growth (using available metrics)
        growth = info.get('earningsQuarterlyGrowth', info.get('revenueGrowth', None))
        if growth is not None:
            growth = growth * 100  # Convert to percentage

        # Calculate EV/Sales
        enterprise_value = info.get('enterpriseValue')
        total_revenue = info.get('totalRevenue')
        ev_sales = None
        if enterprise_value and total_revenue and total_revenue > 0:
            ev_sales = enterprise_value / total_revenue

        return create_ticker_data_dict(symbol, name, price, p_fcf, p_e, growth, ev_sales)
    except Exception as e:
        # Return incomplete data on error (errors suppressed for cleaner multi-threaded output)
        return create_ticker_data_dict(symbol)

# Fetch ticker list
if ticker_file:
    print(f"Reading tickers from file: {ticker_file}")
    tickers = read_tickers_from_file(ticker_file)
    ticker_source = "file"
else:
    print(f"Fetching Nasdaq 100 tickers from Wikipedia...")
    tickers = fetch_nasdaq100_tickers()
    ticker_source = "Nasdaq 100"

print(f"Found {len(tickers)} tickers")
print(f"Scanning for P/FCF < {max_pfcf_threshold}...")
print(f"Using {num_threads} threads for concurrent processing\n")

# Scan all tickers using thread pool
results = []
total = len(tickers)

start_time = time.time()

with ThreadPoolExecutor(max_workers=num_threads) as executor:
    # Submit all tasks
    future_to_ticker = {
        executor.submit(fetch_ticker_data, symbol): symbol
        for symbol in tickers
    }

    # Collect results as they complete (with batched progress updates)
    for i, future in enumerate(as_completed(future_to_ticker), 1):
        data = future.result()  # No need for try-catch since fetch_ticker_data handles all exceptions
        results.append(data)

        # Print progress every 10 tickers to reduce lock contention
        if i % 10 == 0 or i == total:
            print(f"Progress: {i}/{total} tickers processed")

elapsed_time = time.time() - start_time
print(f"\nCompleted scanning {total} tickers in {elapsed_time:.1f} seconds")

# Categorize results
filtered_results = []  # Tickers with P/FCF < threshold
incomplete_results = []  # Tickers with missing P/FCF data

for data in results:
    if data['p_fcf'] is not None and data['growth'] is not None:
        if data['p_fcf'] < max_pfcf_threshold and data['growth'] > MIN_GROWTH_THRESHOLD:
            filtered_results.append(data)
    else:
        incomplete_results.append(data)

# Sort filtered results by P/FCF (ascending - best values first)
filtered_results.sort(key=lambda x: x['p_fcf'])

print(f"\nFound {len(filtered_results)} tickers with P/FCF < {max_pfcf_threshold}")
print(f"{len(incomplete_results)} tickers had incomplete/missing data")

def format_value(value, decimals=2, prefix='', suffix=''):
    """Format numeric value or return N/A for None."""
    if value is None:
        return 'N/A'
    return f"{prefix}{value:.{decimals}f}{suffix}"

def print_results_table(results, title):
    """Print results in formatted table."""
    if not results:
        print(f"\n{title}")
        print("No results to display")
        return

    print(f"\n{title}")
    print("=" * 100)
    print(f"{'Ticker':<8} {'P/FCF':<8} {'P/E':<8} {'Growth%':<10} {'EV/Sales':<10} {'Price':<10} {'Name':<40}")
    print("-" * 100)

    for data in results:
        ticker = data['ticker']
        p_fcf = format_value(data['p_fcf'], 1)
        p_e = format_value(data['p_e'], 1)
        growth = format_value(data['growth'], 1, suffix='%')
        ev_sales = format_value(data['ev_sales'], 2)
        price = format_value(data['price'], 2, prefix='$')
        name = data['name'][:39] if len(data['name']) > 39 else data['name']

        print(f"{ticker:<8} {p_fcf:<8} {p_e:<8} {growth:<10} {ev_sales:<10} {price:<10} {name:<40}")

# Print results
print_results_table(filtered_results, f"Results: Tickers with P/FCF < {max_pfcf_threshold}")

def save_to_csv(filtered_results, incomplete_results, filename):
    """Save results to CSV file."""
    # Prepare data for CSV
    csv_data = []

    # Add filtered results
    for data in filtered_results:
        csv_data.append({
            'Ticker': data['ticker'],
            'Name': data['name'],
            'Price': data['price'],
            'P/FCF': data['p_fcf'],
            'P/E': data['p_e'],
            'Growth%': data['growth'],
            'EV/Sales': data['ev_sales'],
            'Data_Status': 'Complete'
        })

    # Add incomplete results
    for data in incomplete_results:
        csv_data.append({
            'Ticker': data['ticker'],
            'Name': data['name'],
            'Price': data['price'],
            'P/FCF': data['p_fcf'],
            'P/E': data['p_e'],
            'Growth%': data['growth'],
            'EV/Sales': data['ev_sales'],
            'Data_Status': 'Incomplete'
        })

    # Create DataFrame and save
    df = pd.DataFrame(csv_data)
    df.to_csv(filename, index=False)
    print(f"\nResults saved to: {filename}")

# Generate timestamped filename
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
source_name = "custom" if ticker_file else "nasdaq"
csv_filename = f"{source_name}_scan_{timestamp}.csv"

# Save to CSV
save_to_csv(filtered_results, incomplete_results, csv_filename)
