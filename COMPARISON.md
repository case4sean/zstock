# Stock Scanner Comparison

## Two Powerful Scanners for Different Strategies

### scan_nasdaq.py - Value Investing (P/FCF Focus)

**Best for:** Finding undervalued companies with strong cash flow

**Key Metric:** Price-to-Free Cash Flow (P/FCF)
- Lower P/FCF = Better value
- Indicates how much you pay per dollar of free cash flow

**Other Metrics:**
- P/E Ratio
- EPS Growth %
- EV/Sales
- Stock Price

**Usage:**
```bash
python3 scan_nasdaq.py --max-pfcf 10 --threads 20
```

**Real Results (Feb 2026):**
```
Found 11 tickers with P/FCF < 10.0:
- PRU: P/FCF 2.7, P/E 9.8, Growth 31.2%
- CINF: P/FCF 4.2, P/E 10.8, Growth 66.9%
- PDD: P/FCF 1.7, P/E 10.3, Growth 17.4%
```

**When to use:**
- Looking for deeply undervalued stocks
- Focus on cash flow generation
- Value investing strategy

---

### sp500_eps.py - Earnings Focus (EPS Analysis)

**Best for:** Analyzing earnings power and growth potential

**Key Metrics:**
- EPS (Earnings Per Share) - Current profitability
- Forward EPS - Expected earnings
- EPS Growth % - Earnings momentum

**Other Metrics:**
- P/E Ratios (Trailing and Forward)
- Market Cap
- Sector Classification
- Quarterly Growth

**Usage:**
```bash
python3 sp500_eps.py --min-eps 5 --max-pe 20 --min-growth 15 --threads 20
```

**Real Results (Feb 2026):**
```
Found 51 tickers matching criteria (EPS >= 5, P/E <= 20, Growth >= 15%):
- GS: EPS $51.32, P/E 16.7, Growth 26.7%
- REGN: EPS $41.51, P/E 18.8, Growth 26.5%
- ADBE: EPS $16.69, P/E 15.7, Growth 58.2%
```

**When to use:**
- Evaluating earnings quality
- Finding growth at reasonable prices
- Comparing companies within sectors
- S&P 500 stock screening

---

## Side-by-Side Comparison

| Feature | scan_nasdaq.py | sp500_eps.py |
|---------|----------------|--------------|
| **Primary Focus** | Cash Flow | Earnings |
| **Default Source** | Nasdaq 100 | S&P 500 |
| **Key Metric** | P/FCF | EPS |
| **Best For** | Value investing | Growth investing |
| **Filters** | P/FCF, P/E, Growth, EV/Sales | EPS, Forward EPS, P/E, Growth |
| **Output** | Best values first (P/FCF) | Highest EPS first |
| **Typical Results** | 10-50 tickers | 50-350 tickers |
| **Speed (500 tickers)** | ~10-20 sec (20 threads) | ~4-5 sec (20 threads) |

---

## Strategy Recommendations

### Conservative Value Investing
Use **scan_nasdaq.py** with tight filters:
```bash
python3 scan_nasdaq.py --max-pfcf 8 --threads 20
```

### Quality Growth Stocks
Use **sp500_eps.py** with balanced filters:
```bash
python3 sp500_eps.py --min-eps 10 --max-pe 20 --min-growth 15
```

### High Growth Opportunities
Use **sp500_eps.py** focusing on growth:
```bash
python3 sp500_eps.py --min-growth 30 --threads 20
```

### Deep Value Plays
Use **scan_nasdaq.py** with lenient filters:
```bash
python3 scan_nasdaq.py --max-pfcf 12 --threads 20
```

---

## Using Both for Better Decisions

**Step 1:** Find undervalued candidates with scan_nasdaq.py
```bash
python3 scan_nasdaq.py --max-pfcf 10 --threads 20
# Results: PRU, CINF, CNC, AIZ, TRV...
```

**Step 2:** Analyze their earnings profile with sp500_eps.py
```bash
echo -e "PRU\nCINF\nCNC\nAIZ\nTRV" > value_candidates.txt
python3 sp500_eps.py --ticker-file value_candidates.txt
```

**Step 3:** Compare results
- Low P/FCF + High EPS Growth = Strong candidate
- Low P/FCF + Low/Negative EPS = Risky play
- High P/FCF + High EPS Growth = Growth stock

---

## Real-World Examples

### Example 1: Finding the Best of Both Worlds

**Goldman Sachs (GS):**
- P/FCF: Not in top 10 (moderate cash flow)
- EPS: $51.32 (2nd highest in S&P 500)
- P/E: 16.7 (reasonable valuation)
- Growth: 26.7% (strong momentum)
- **Verdict:** Quality growth at fair price

**Prudential Financial (PRU):**
- P/FCF: 2.7 (extremely undervalued)
- EPS: $9.99 (solid earnings)
- P/E: 9.8 (very low)
- Growth: 55.1% (strong growth)
- **Verdict:** Deep value with growth potential

### Example 2: Red Flags

**High P/FCF + Low EPS = Overvalued**
- May have temporary earnings boost
- Cash generation doesn't support valuation

**Low P/FCF + Negative EPS = Turnaround Play**
- Risky but potentially rewarding
- Requires deeper research

---

## Performance Comparison

### Actual Test Results

**scan_nasdaq.py (Nasdaq 100):**
- Tickers scanned: 101
- Time: 9.0 seconds
- Speed: 11.2 tickers/second

**sp500_eps.py (S&P 500):**
- Tickers scanned: 503
- Time: 3.8 seconds
- Speed: 132.4 tickers/second

**sp500_eps.py is 12x faster per ticker!**
(Optimized specifically for EPS data retrieval)

---

## Which Scanner Should You Use?

### Use scan_nasdaq.py when:
- ✅ You follow value investing principles
- ✅ Free cash flow is your priority
- ✅ You want to find deeply undervalued stocks
- ✅ You're looking at Nasdaq 100 specifically

### Use sp500_eps.py when:
- ✅ You care about earnings quality
- ✅ You want to analyze S&P 500 specifically
- ✅ You need sector information
- ✅ You're comparing earnings growth rates
- ✅ You need the fastest possible scan

### Use BOTH when:
- ✅ You want comprehensive analysis
- ✅ You're building a balanced portfolio
- ✅ You want to verify investment thesis
- ✅ You're comparing multiple strategies

---

## Quick Commands Reference

**Find Best Value Stocks:**
```bash
python3 scan_nasdaq.py --max-pfcf 8 --threads 20
```

**Find Quality Growth Stocks:**
```bash
python3 sp500_eps.py --min-eps 10 --max-pe 18 --min-growth 20 --threads 20
```

**Analyze Custom Watchlist:**
```bash
python3 scan_nasdaq.py --ticker-file watchlist.txt --max-pfcf 15
python3 sp500_eps.py --ticker-file watchlist.txt
```

**Complete S&P 500 Analysis:**
```bash
python3 sp500_eps.py --threads 20 > sp500_analysis.txt
```

---

## Summary

Both scanners are powerful tools for different investment strategies:

- **scan_nasdaq.py**: Focus on cash flow and finding undervalued gems
- **sp500_eps.py**: Focus on earnings power and growth potential

Using them together provides a complete picture of a company's:
1. Cash generation ability (P/FCF)
2. Earnings quality (EPS)
3. Growth trajectory (EPS Growth)
4. Valuation fairness (P/E ratios)

The best investors use multiple metrics! 📊
