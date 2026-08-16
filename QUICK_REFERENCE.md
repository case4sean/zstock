# Quick Reference Guide

## 🚀 Running Scans

### S&P 500 EPS Scanner
```bash
source venv/bin/activate

# Basic scan
python3 sp500_eps.py --threads 20

# With filters
python3 sp500_eps.py --min-eps 5 --max-pe 20 --min-growth 15 --threads 20

# Custom ticker list
python3 sp500_eps.py --ticker-file my_stocks.txt
```

### Nasdaq P/FCF Scanner
```bash
source venv/bin/activate

# Basic scan
python3 scan_nasdaq.py --threads 20

# With filters
python3 scan_nasdaq.py --max-pfcf 10 --threads 20

# Custom ticker list
python3 scan_nasdaq.py --ticker-file my_stocks.txt --max-pfcf 12
```

### Investment Simulator
```bash
source venv/bin/activate

# Basic simulation
python3 playtick.py --ticker SPY

# Custom parameters
python3 playtick.py --ticker JEPQ --start 2024-01-01 --end 2025-01-01 --weekly-investment 200
```

---

## 📊 Analyzing Results

### S&P 500 Statistics (Average EPS, P/E)

```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print(f"📊 Analysis: {csv}\n")
print(f"Average EPS: ${complete['EPS'].mean():.2f}")
print(f"Average Forward EPS: ${complete['Forward_EPS'].mean():.2f}")
print(f"Average P/E: {complete['PE_Ratio'].mean():.2f}x")
print(f"Average Forward P/E: {complete['Forward_PE'].mean():.2f}x")
print(f"\nMedian EPS: ${complete['EPS'].median():.2f}")
print(f"Median P/E: {complete['PE_Ratio'].median():.2f}x")
EOF
```

### Nasdaq Statistics (Average P/FCF)

```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('nasdaq_scan_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print(f"📊 Analysis: {csv}\n")
print(f"Average P/FCF: {complete['P/FCF'].mean():.2f}x")
print(f"Median P/FCF: {complete['P/FCF'].median():.2f}x")
print(f"Average P/E: {complete['P/E'].mean():.2f}x")
print(f"Average Growth: {complete['Growth%'].mean():.1f}%")
EOF
```

### Top Performers

```bash
# Top 10 by EPS
python3 << 'EOF'
import pandas as pd
import glob
csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
print("🏆 Top 10 by EPS:")
print(df.nlargest(10, 'EPS')[['Ticker', 'Name', 'EPS', 'PE_Ratio', 'Sector']])
EOF

# Top 10 by P/FCF (best value)
python3 << 'EOF'
import pandas as pd
import glob
csv = sorted(glob.glob('nasdaq_scan_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']
print("💎 Top 10 Best P/FCF (Most Undervalued):")
print(complete.nsmallest(10, 'P/FCF')[['Ticker', 'P/FCF', 'P/E', 'Growth%', 'Price']])
EOF
```

### Sector Analysis

```bash
# EPS by Sector
python3 << 'EOF'
import pandas as pd
import glob
csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print("📊 Average EPS by Sector:")
sector = complete.groupby('Sector')['EPS'].agg(['mean', 'median', 'count']).round(2)
sector.columns = ['Avg_EPS', 'Med_EPS', 'Count']
print(sector.sort_values('Avg_EPS', ascending=False))
EOF

# P/E by Sector
python3 << 'EOF'
import pandas as pd
import glob
csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print("📊 Average P/E by Sector:")
sector = complete.groupby('Sector')['PE_Ratio'].agg(['mean', 'median', 'count']).round(2)
sector.columns = ['Avg_PE', 'Med_PE', 'Count']
print(sector.sort_values('Avg_PE', ascending=False))
EOF
```

---

## 🎯 Custom Filters

### Find Value Growth Stocks
```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)

# High growth + Low P/E + High EPS
filtered = df[(df['EPS_Growth_%'] > 20) & (df['PE_Ratio'] < 25) & (df['EPS'] > 5)]
print(f"Found {len(filtered)} value growth stocks")
print(filtered[['Ticker', 'Name', 'EPS', 'EPS_Growth_%', 'PE_Ratio', 'Sector']].sort_values('EPS', ascending=False))
EOF
```

### Find Deep Value Stocks
```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('nasdaq_scan_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

# Low P/FCF + Low P/E + Positive Growth
filtered = complete[(complete['P/FCF'] < 8) & (complete['P/E'] < 15) & (complete['Growth%'] > 10)]
print(f"Found {len(filtered)} deep value stocks")
print(filtered[['Ticker', 'Name', 'P/FCF', 'P/E', 'Growth%', 'Price']].sort_values('P/FCF'))
EOF
```

### Find High Growth Tech
```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)

# Tech sector + High growth
tech = df[df['Sector'] == 'Technology']
filtered = tech[(tech['EPS_Growth_%'] > 30) & (tech['EPS'] > 3)]
print(f"Found {len(filtered)} high-growth tech stocks")
print(filtered[['Ticker', 'Name', 'EPS', 'EPS_Growth_%', 'PE_Ratio']].sort_values('EPS_Growth_%', ascending=False))
EOF
```

---

## 🔍 Compare Stocks

### Side-by-Side Comparison
```bash
python3 << 'EOF'
import pandas as pd
import glob

# Compare specific tickers
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)

comparison = df[df['Ticker'].isin(tickers)]
print("📊 Stock Comparison:")
print(comparison[['Ticker', 'Name', 'Price', 'EPS', 'PE_Ratio', 'EPS_Growth_%', 'Market_Cap']].sort_values('EPS', ascending=False))
EOF
```

### Compare Sectors
```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

# Compare multiple metrics by sector
comparison = complete.groupby('Sector').agg({
    'EPS': 'mean',
    'PE_Ratio': 'mean',
    'EPS_Growth_%': 'mean',
    'Ticker': 'count'
}).round(2)
comparison.columns = ['Avg_EPS', 'Avg_PE', 'Avg_Growth', 'Count']
print(comparison.sort_values('Avg_EPS', ascending=False))
EOF
```

---

## 💾 Export Custom Results

### Export to New CSV
```bash
python3 << 'EOF'
import pandas as pd
import glob
from datetime import datetime

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)

# Custom filter
filtered = df[(df['EPS'] > 10) & (df['PE_Ratio'] < 20)]

# Save to new file
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
output = f"custom_filter_{timestamp}.csv"
filtered.to_csv(output, index=False)
print(f"Saved {len(filtered)} stocks to: {output}")
EOF
```

---

## 📈 Trending Analysis

### Growth Leaders
```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)

# Top growth with data quality
growth = df[(df['EPS_Growth_%'].notna()) & (df['EPS'] > 2)]
top_growth = growth.nlargest(20, 'EPS_Growth_%')
print("🚀 Top 20 Growth Leaders:")
print(top_growth[['Ticker', 'Name', 'EPS', 'EPS_Growth_%', 'PE_Ratio', 'Sector']])
EOF
```

### Value Leaders
```bash
python3 << 'EOF'
import pandas as pd
import glob

csv = sorted(glob.glob('nasdaq_scan_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

# Best P/FCF with quality metrics
value = complete[(complete['P/FCF'] < 15) & (complete['Growth%'] > 10)]
print("💎 Value Leaders (Low P/FCF + Growth):")
print(value.nsmallest(20, 'P/FCF')[['Ticker', 'Name', 'P/FCF', 'P/E', 'Growth%', 'Price']])
EOF
```

---

## 🔄 Compare Multiple Scans

### Track Changes Over Time
```bash
python3 << 'EOF'
import pandas as pd
import glob

files = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[:2]

if len(files) < 2:
    print("Need at least 2 scans to compare")
else:
    df1 = pd.read_csv(files[0])
    df2 = pd.read_csv(files[1])

    complete1 = df1[df1['Data_Status'] == 'Complete']
    complete2 = df2[df2['Data_Status'] == 'Complete']

    print(f"Latest: {files[0]}")
    print(f"  Avg EPS: ${complete1['EPS'].mean():.2f}")
    print(f"  Avg P/E: {complete1['PE_Ratio'].mean():.2f}x")

    print(f"\nPrevious: {files[1]}")
    print(f"  Avg EPS: ${complete2['EPS'].mean():.2f}")
    print(f"  Avg P/E: {complete2['PE_Ratio'].mean():.2f}x")

    eps_change = complete1['EPS'].mean() - complete2['EPS'].mean()
    print(f"\n📊 Change in Avg EPS: ${eps_change:+.2f}")
EOF
```

---

## ⚡ Quick Tips

**Always activate venv first:**
```bash
source venv/bin/activate
```

**List recent scans:**
```bash
ls -lt *_eps_*.csv *_scan_*.csv | head -10
```

**View CSV in terminal:**
```bash
python3 -c "import pandas as pd; df=pd.read_csv('sp500_eps_2026-02-28_13-11.csv'); print(df.head(20))"
```

**Count complete vs incomplete:**
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('sp500_eps_2026-02-28_13-11.csv')
print(df['Data_Status'].value_counts())
EOF
```

---

## 📚 More Information

- **CLAUDE.md** - Full documentation and architecture
- **README.md** - Project overview and setup
- **COMPARISON.md** - Scanner comparison guide
- **PERFORMANCE.md** - Performance benchmarks

---

**Pro Tip:** Bookmark this file for quick access to commonly used commands! 🔖
