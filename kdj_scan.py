import yfinance as yf
import pandas as pd
import numpy as np
import argparse
import hashlib
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

parser = argparse.ArgumentParser(description='Scan stocks for KDJ A or Y signals')
parser.add_argument('--ticker-file', type=str, default='tickers.txt',
                    help='Path to text file with ticker symbols (default: tickers.txt)')
parser.add_argument('--period', type=str, default='6mo',
                    help='History period for yfinance (default: 6mo)')
parser.add_argument('--threads', type=int, default=10,
                    help='Number of concurrent threads (default: 10)')
parser.add_argument('--weekly', action='store_true',
                    help='Compute KDJ based on weekly close bars instead of daily (default: False)')
parser.add_argument('--feeder', type=str, default=None,
                    help='Feeder identifier for filenames. Defaults to a hash of the ticker file path. '
                         'Different feeders keep separate scan files even on the same day.')
args = parser.parse_args()


def feeder_id():
    if args.feeder:
        return args.feeder
    raw = args.ticker_file
    if os.path.isfile(raw):
        raw = os.path.abspath(raw)
    return hashlib.sha1(raw.encode()).hexdigest()[:8]


def read_tickers(filepath):
    try:
        with open(filepath) as f:
            return [line.strip().upper() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: file not found: {filepath}")
        exit(1)


def weighted_sma(series, n, m, init=50.0):
    """Chinese-style SMA: sma[i] = (m * x[i] + (n-m) * sma[i-1]) / n"""
    values = series.values.astype(float)
    result = np.full(len(values), np.nan)
    # Find first non-NaN to seed
    for i, v in enumerate(values):
        if not np.isnan(v):
            result[i] = init
            start = i
            break
    else:
        return pd.Series(result, index=series.index)

    for i in range(start + 1, len(values)):
        prev = result[i - 1] if not np.isnan(result[i - 1]) else init
        x = values[i] if not np.isnan(values[i]) else prev
        result[i] = (m * x + (n - m) * prev) / n

    return pd.Series(result, index=series.index)


def compute_kdj(df, rsv_period=9):
    """Compute KDJ: RSV=(C-LLV9)/(HHV9-LLV9)*100, K=SMA(RSV,3,1), D=SMA(K,3,1)"""
    low_min = df['Low'].rolling(rsv_period).min()
    high_max = df['High'].rolling(rsv_period).max()
    denom = (high_max - low_min).replace(0, np.nan)
    rsv = (df['Close'] - low_min) / denom * 100
    rsv = rsv.fillna(50.0)
    k = weighted_sma(rsv, n=3, m=1, init=50.0)
    d = weighted_sma(k, n=3, m=1, init=50.0)
    return k, d


def to_weekly(df):
    """Resample daily OHLC bars to weekly bars (close uses week-ending close)."""
    weekly = pd.DataFrame({
        'High': df['High'].resample('W').max(),
        'Low': df['Low'].resample('W').min(),
        'Close': df['Close'].resample('W').last(),
    }).dropna()
    return weekly


def check_signals(symbol, period, weekly=False):
    try:
        df = yf.Ticker(symbol).history(period=period)
        if df.empty:
            return None

        if weekly:
            df = to_weekly(df)

        if len(df) < 20:
            return None

        k, d = compute_kdj(df)

        k_now = k.iloc[-1]
        k_prev = k.iloc[-2]
        d_now = d.iloc[-1]
        close = df['Close'].iloc[-1]

        # A: K>=64, K turning down, K>=D, D<=82
        signal_a = k_now >= 64 and k_now < k_prev and k_now >= d_now and d_now <= 82
        # Y: K<=31, K turning up, K<=D, D>=18
        signal_y = k_now <= 31 and k_now > k_prev and k_now <= d_now and d_now >= 18

        if signal_a or signal_y:
            return {
                'ticker': symbol,
                'signal': 'A' if signal_a else 'Y',
                'K': round(k_now, 2),
                'D': round(d_now, 2),
                'close': round(close, 2),
            }
        return None
    except Exception:
        return None


tickers = read_tickers(args.ticker_file)
print(f"Loaded {len(tickers)} tickers from {args.ticker_file}")
print(f"Scanning for KDJ A/Y signals (period={args.period}, threads={args.threads}, weekly={args.weekly})...\n")

results = []
total = len(tickers)
start_time = time.time()

with ThreadPoolExecutor(max_workers=args.threads) as executor:
    futures = {executor.submit(check_signals, sym, args.period, args.weekly): sym for sym in tickers}
    for i, future in enumerate(as_completed(futures), 1):
        result = future.result()
        if result:
            results.append(result)
        if i % 10 == 0 or i == total:
            print(f"Progress: {i}/{total}")

elapsed = time.time() - start_time
print(f"\nCompleted in {elapsed:.1f}s — {len(results)} signals found\n")

if results:
    results.sort(key=lambda x: (x['signal'], x['ticker']))
    print(f"{'Ticker':<8} {'Signal':<8} {'K':<8} {'D':<8} {'Close'}")
    print("-" * 45)
    for r in results:
        print(f"{r['ticker']:<8} {r['signal']:<8} {r['K']:<8} {r['D']:<8} {r['close']}")

    today = datetime.now()
    freq = "weekly" if args.weekly else "daily"
    if args.weekly:
        date_key = (today - timedelta(days=today.weekday()) + timedelta(days=4)).strftime('%Y-%m-%d')
    else:
        date_key = today.strftime('%Y-%m-%d')
    csv_file = f"kdj_scan_{freq}_{feeder_id()}_{date_key}.csv"
    pd.DataFrame(results).to_csv(csv_file, index=False)
    print(f"\nSaved to {csv_file} (feeder={feeder_id()})")
else:
    print("No A or Y signals found.")
