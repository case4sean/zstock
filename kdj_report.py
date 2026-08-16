import glob
import re
import datetime
import argparse
import pandas as pd


def collect_files(pattern='kdj_scan_*.csv', frequency='all'):
    files = sorted(glob.glob(pattern))
    per_date = {}
    for f in files:
        # kdj_scan_{freq}_{feeder}_{date}.csv  |  kdj_scan_{freq}_{date}.csv  |  kdj_scan_{date}.csv
        m = re.search(r'kdj_scan_(weekly|daily)_([0-9a-f]{8}|[^_]+)_(\d{4}-\d{2}-\d{2})\.csv', f)
        freq = None
        if m:
            freq = m.group(1)
            date = m.group(3)
        else:
            m = re.search(r'kdj_scan_(weekly|daily)_(\d{4}-\d{2}-\d{2})\.csv', f)
            if m:
                freq = m.group(1)
                date = m.group(2)
            else:
                m = re.search(r'kdj_scan_(\d{4}-\d{2}-\d{2})\.csv', f)
                if not m:
                    continue
                freq = 'daily'
                date = m.group(1)
        freq = freq or 'daily'
        if frequency not in ('all',) and freq != frequency:
            continue
        per_date.setdefault(date, []).append((f, date, freq))
    return {d: [(f, freq) for f, _, freq in sorted(lst, key=lambda x: x[1])]
            for d, lst in per_date.items()}


def build_report(pattern='kdj_scan_*.csv', outfile='kdj_report.html', frequency='all'):
    per_date = collect_files(pattern, frequency)
    frames = []
    for date, lst in per_date.items():
        for f, freq in lst:
            df = pd.read_csv(f)
            df['date'] = date
            df['freq'] = freq
            frames.append(df)

    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df.drop_duplicates(subset=['ticker', 'date'], keep='last')
    pivot = all_df.pivot_table(index='ticker', columns='date', values=['signal', 'close'], aggfunc='last')

    dates = sorted(per_date.keys())

    def group_of(t):
        sigs = [pivot.loc[t, ('signal', d)] for d in dates]
        if any(s == 'A' for s in sigs):
            return 0
        if any(s == 'Y' for s in sigs):
            return 1
        return 2

    pivot['__rank'] = [group_of(t) for t in pivot.index]
    pivot['__tick'] = pivot.index
    pivot = pivot.sort_values(['__rank', '__tick']).drop(columns=['__rank', '__tick'])

    rows_html = ""
    for ticker in pivot.index:
        cells = []
        for d in dates:
            sig = pivot.loc[ticker, ('signal', d)]
            cl = pivot.loc[ticker, ('close', d)]
            if pd.isna(sig):
                cells.append('<td></td>')
            else:
                color = '#e74c3c' if sig == 'A' else '#2e86de'
                cells.append(
                    f'<td><span class="sig" style="background:{color}">{sig}</span> {cl:.2f}</td>')
        rows_html += f'<tr><td class="tick">{ticker}</td>{"".join(cells)}</tr>\n'

    thead = '<th>Ticker</th>'
    for d in dates:
        sigs = pivot.loc[:, ('signal', d)].dropna()
        cnt_a = int((sigs == 'A').sum())
        cnt_y = int((sigs == 'Y').sum())
        thead += f'<th>{d}<br><span class="cnt">{cnt_a}-{cnt_y}</span></th>'

    n_dates = len(dates)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>KDJ Scan Report</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }}
h1 {{ font-size: 20px; }}
table {{ border-collapse: collapse; font-size: 13px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
th {{ background: #f5f5f5; }}
.tick {{ font-weight: 600; }}
.sig {{ display: inline-block; color: #fff; border-radius: 3px; padding: 0 5px; font-weight: 700; }}
.cnt {{ display: block; color: #999; font-weight: 400; font-size: 11px; }}
.filter-btn {{ margin: 0 4px 10px 0; padding: 4px 12px; cursor: pointer; border: 1px solid #aaa;
               border-radius: 4px; background: #f5f5f5; font-size: 13px; }}
.filter-btn.active {{ background: #2e86de; color: #fff; border-color: #2e86de; }}
</style></head>
<body>
<h1>KDJ Scan Report</h1>
<p><a href="/" style="color:#2e86de; font-size:13px;">← Back to Scanner</a></p>
<p>Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Frequency: {frequency} | Merged from kdj_scan files | Sorted: A first, then Y, alphabetical within group | A=red (sell), Y=blue (buy) | Header counts = A count, then Y count (A-Y)</p>
<div>
  <button class="filter-btn" onclick="setDays(3)">Last 3 Days</button>
  <button class="filter-btn" onclick="setDays(5)">Last 5 Days</button>
  <button class="filter-btn active" onclick="setDays(0)">All Days</button>
</div>
<table id="kdjtable">
<thead><tr>{thead}</tr></thead>
<tbody>
{rows_html}</tbody>
</table>
<script>
var TOTAL_COLS = {n_dates};
function setDays(n) {{
  var table = document.getElementById('kdjtable');
  var tbody = table.tBodies[0];
  var rows = table.rows;
  var showFrom = (n === 0) ? 0 : Math.max(0, TOTAL_COLS - n);

  // show/hide columns (row 0 = thead)
  for (var r = 0; r < rows.length; r++) {{
    var cells = rows[r].cells;
    for (var c = 1; c < cells.length; c++) {{
      cells[c].style.display = (c - 1 >= showFrom) ? '' : 'none';
    }}
  }}

  // classify each data row by signals in the visible window, then re-sort
  var dataRows = Array.from(tbody.rows);
  dataRows.forEach(function(row) {{
    var hasA = false, hasY = false;
    var cells = row.cells;
    for (var c = showFrom + 1; c < cells.length; c++) {{
      var sig = cells[c].querySelector('.sig');
      if (sig) {{
        if (sig.textContent === 'A') hasA = true;
        else if (sig.textContent === 'Y') hasY = true;
      }}
    }}
    row.style.display = (hasA || hasY) ? '' : 'none';
    // 0=A, 1=Y, 2=none
    row._group = hasA ? 0 : (hasY ? 1 : 2);
    row._tick = row.cells[0].textContent;
  }});

  dataRows.sort(function(a, b) {{
    if (a._group !== b._group) return a._group - b._group;
    return a._tick < b._tick ? -1 : a._tick > b._tick ? 1 : 0;
  }});
  dataRows.forEach(function(row) {{ tbody.appendChild(row); }});

  // update active button
  var btns = document.querySelectorAll('.filter-btn');
  btns.forEach(function(b) {{ b.classList.remove('active'); }});
  event.target.classList.add('active');
}}
</script>
</body></html>"""

    with open(outfile, 'w') as fh:
        fh.write(html)
    print(f"Merged {len(all_df)} rows from {len(frames)} files [{frequency}], wrote {outfile}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate KDJ HTML report')
    parser.add_argument('--frequency', choices=['daily', 'weekly', 'all'], default='daily',
                        help='Which scan frequency to include (default: daily)')
    parser.add_argument('--outfile', default=None,
                        help='Output HTML file (default: kdj_report_<freq>.html)')
    args = parser.parse_args()
    if not args.outfile:
        args.outfile = f"kdj_report_{args.frequency}.html"
    build_report(outfile=args.outfile, frequency=args.frequency)
