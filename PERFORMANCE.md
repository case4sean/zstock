# Performance Comparison

## Multi-Threading Benefits

The scanner now uses concurrent processing with Python's ThreadPoolExecutor for significantly faster scans.

### Speed Comparison

| Tickers | Sequential (old) | Multi-threaded (10 threads) | Multi-threaded (20 threads) | Speedup |
|---------|------------------|------------------------------|------------------------------|---------|
| 25      | ~12.5 seconds   | ~1-2 seconds                 | ~1-2 seconds                 | **10x** |
| 100     | ~3-4 minutes    | ~15-30 seconds               | ~10-20 seconds               | **12x** |
| 500     | ~15-20 minutes  | ~1-2 minutes                 | ~45-90 seconds               | **15x** |

### Recommended Thread Counts

- **10 threads (default):** Good balance of speed and API stability
- **15-20 threads:** Faster for large scans, may hit API rate limits occasionally
- **5 threads:** More conservative, better for unstable connections

### Example Commands

Fast scan with 20 threads:
```bash
python3 scan_nasdaq.py --threads 20 --max-pfcf 10
```

Conservative scan with 5 threads:
```bash
python3 scan_nasdaq.py --threads 5 --max-pfcf 10
```

Custom ticker list with 15 threads:
```bash
python3 scan_nasdaq.py --ticker-file tickers.txt --threads 15
```

## Technical Details

- Uses `concurrent.futures.ThreadPoolExecutor` for parallel API requests
- Thread-safe progress tracking with `threading.Lock`
- Each thread makes independent yfinance API calls
- No artificial delays between requests (removed `time.sleep()`)
- Results collected and aggregated as threads complete
