import yfinance as yf
import pandas as pd
import numpy as np
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Stock investment simulation with DCA and dividend reinvestment')
parser.add_argument('--ticker', type=str, default='JEPQ', help='Stock ticker symbol (default: JEPQ)')
parser.add_argument('--start', type=str, default='2024-01-01', help='Start date in YYYY-MM-DD format (default: 2024-01-01)')
parser.add_argument('--end', type=str, default='2025-01-01', help='End date in YYYY-MM-DD format (default: 2025-01-01)')
parser.add_argument('--buy-day', type=int, default=2, help='Day of week to buy (0=Mon, 1=Tue, 2=Wed, etc.) (default: 2)')
parser.add_argument('--weekly-investment', type=float, default=100, help='Weekly investment amount in dollars (default: 100)')
args = parser.parse_args()

ticker = args.ticker
buy_day = args.buy_day
start_date = args.start
end_date = args.end
weekly_investment = args.weekly_investment

# 获取历史数据
data = yf.download(ticker, start=start_date, end=end_date, progress=False)

# Check if data was downloaded successfully
if data.empty:
    print(f"Error: No data found for ticker '{ticker}'. Please check the ticker symbol and date range.")
    exit(1)

# 假设每周定投
total_investment = 0
shares_held = 0

asset = yf.Ticker(ticker)
dividends = asset.dividends

# Filter dividends to the date range and handle empty dividends
if not dividends.empty and len(dividends) > 0:
    dividends.index = dividends.index.tz_convert(None).normalize()
    # Filter dividends within the date range
    dividends = dividends[(dividends.index >= start_date) & (dividends.index <= end_date)]
    dividend_dates = dividends.index
else:
    # No dividends, create empty index
    dividend_dates = pd.DatetimeIndex([])


# 生成2023年到2024年之间的所有自然日
all_dates = pd.date_range(start=start_date, end=end_date, freq='D')

# 选出所有周三
selected_dates = all_dates[all_dates.weekday == buy_day]

# 初始化一个列表来存储每周的投资日
investment_days = []

for trade_day in selected_dates:
    if trade_day in data.index:
        investment_days.append(trade_day)
    else:
        next_trading_day = trade_day
        while next_trading_day not in data.index:
            next_trading_day += pd.Timedelta(days=1)
            # 防止超出数据范围
            if next_trading_day > data.index[-1]:
                break
        if next_trading_day in data.index:
            investment_days.append(next_trading_day)

trading_days = investment_days.copy()

# 将分红日期添加到投资日中
for dividend_date in dividend_dates:
    if dividend_date not in investment_days and dividend_date in data.index:
        investment_days.append(dividend_date)

# 输出结果
investment_days_data = data.loc[investment_days].sort_index()

# 模拟投资
for index, row in investment_days_data.iterrows():
    current_price = float(row['Close'].iloc[0])
    if index in dividends.index:
        shares_bought_from_dividend = dividends[index] * shares_held / current_price
        shares_held += shares_bought_from_dividend 

    if index not in trading_days:
        continue
    # 购买股票
    shares_bought = weekly_investment / current_price
    shares_held += shares_bought
    total_investment += weekly_investment
        
# 计算最终投资组合价值
final_value = shares_held * float(data['Close'].iloc[-1].iloc[0])

print(f"Total Investment: ${total_investment:.2f}")
print(f"Final Portfolio Value: ${final_value:.2f}; shares_held: {shares_held:.2f}")
print(f"Total Return: {((final_value - total_investment) / total_investment) * 100:.2f}%")
