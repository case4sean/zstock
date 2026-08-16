import glob
import os
import subprocess
import sys
import time
from datetime import datetime

from flask import Flask, render_template, request, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', BASE_DIR)
DEFAULT_TICKER_FILE = os.environ.get('DEFAULT_TICKER_FILE', 'nasdaq100_sp500.txt')
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))

os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)


def latest_scan_csv(frequency=None):
    pattern = 'kdj_scan_*.csv'
    if frequency == 'weekly':
        pattern = 'kdj_scan_weekly_*.csv'
    elif frequency == 'daily':
        pattern = 'kdj_scan_daily_*.csv'
    import re
    files = glob.glob(os.path.join(DATA_DIR, pattern))
    if not files:
        return None
    return max(files, key=lambda f: re.search(r'(\d{4}-\d{2}-\d{2})', f).group(1) if re.search(r'(\d{4}-\d{2}-\d{2})', f) else '')


def latest_report_html(frequency='daily'):
    path = os.path.join(DATA_DIR, f'kdj_report_{frequency}.html')
    return path if os.path.exists(path) else None


def available_ticker_files():
    dirs = [DATA_DIR, BASE_DIR]
    files = set()
    for d in dirs:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.txt') and os.path.isfile(os.path.join(d, f)):
                    files.add(f)
    return sorted(files)


def resolve_ticker_file(name):
    for d in [DATA_DIR, BASE_DIR]:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None


def count_tickers(name):
    p = resolve_ticker_file(name)
    if not p:
        return 0
    with open(p) as fh:
        return sum(1 for line in fh if line.strip())


@app.route('/')
def index():
    ticker_files = available_ticker_files()
    return render_template(
        'index.html',
        ticker_files=ticker_files,
        default_ticker_file=DEFAULT_TICKER_FILE,
        default_ticker_count=count_tickers(DEFAULT_TICKER_FILE),
        report_exists=latest_report_html() is not None,
        latest_scan=latest_scan_csv(),
        default_frequency='daily',
    )


@app.route('/scan', methods=['POST'])
def scan():
    threads = request.form.get('threads', '20')
    period = request.form.get('period', '6mo')
    frequency = request.form.get('frequency', 'daily')
    if frequency not in ('daily', 'weekly'):
        frequency = 'daily'

    uploaded = request.files.get('ticker_file')
    if uploaded and uploaded.filename:
        upload_path = os.path.join(DATA_DIR, 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        ticker_file = os.path.join(upload_path, uploaded.filename)
        uploaded.save(ticker_file)
        source_label = f'uploaded: {uploaded.filename}'
    else:
        name = request.form.get('ticker_file_select') or DEFAULT_TICKER_FILE
        ticker_file = resolve_ticker_file(name)
        if not ticker_file:
            return render_template('index.html', error=f'Ticker file not found: {name}',
                                   ticker_files=available_ticker_files(),
                                   default_ticker_file=DEFAULT_TICKER_FILE,
                                   report_exists=latest_report_html() is not None,
                                   latest_scan=latest_scan_csv()), 400
        source_label = name

    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, 'kdj_scan.py'),
        '--ticker-file', ticker_file,
        '--threads', threads,
        '--period', period,
    ]
    if frequency == 'weekly':
        cmd.append('--weekly')

    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=DATA_DIR)
    elapsed = time.time() - start

    output = proc.stdout
    if proc.returncode != 0:
        output = output + '\n' + proc.stderr

    new_scan = latest_scan_csv(frequency)
    results = []
    if new_scan:
        results = parse_scan_csv(new_scan)

    return render_template(
        'result.html',
        output=output,
        returncode=proc.returncode,
        elapsed=round(elapsed, 1),
        source_label=source_label,
        threads=threads,
        period=period,
        frequency=frequency,
        results=results,
        scan_file=os.path.basename(new_scan) if new_scan else None,
    )


def parse_scan_csv(csv_path):
    import csv
    rows = []
    with open(csv_path, newline='') as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows


@app.route('/report')
def report():
    frequency = request.args.get('frequency', 'daily')
    if frequency not in ('daily', 'weekly', 'all'):
        frequency = 'daily'
    report_py = os.path.join(BASE_DIR, 'kdj_report.py')
    if os.path.exists(report_py):
        subprocess.run([sys.executable, report_py, '--frequency', frequency],
                       capture_output=True, cwd=DATA_DIR)
    path = latest_report_html(frequency)
    if not path:
        return render_template('index.html', error='No report generated yet. Run a scan first.',
                               ticker_files=available_ticker_files(),
                               default_ticker_file=DEFAULT_TICKER_FILE,
                               report_exists=False,
                               latest_scan=latest_scan_csv()), 404
    return send_file(path)


if __name__ == '__main__':
    app.run(debug=False, host=HOST, port=PORT)
