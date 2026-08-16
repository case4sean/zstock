FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    DATA_DIR=/app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py kdj_scan.py kdj_report.py playtick.py scan_nasdaq.py sp500_eps.py sp500_report.py ./
COPY templates/ ./templates/
COPY nasdaq100_sp500.txt ./
COPY etf.txt staging.txt ./

RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
