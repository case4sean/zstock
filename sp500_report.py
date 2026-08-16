import pandas as pd
import glob

csv = sorted(glob.glob('sp500_eps_*.csv'), reverse=True)[0]
df = pd.read_csv(csv)
complete = df[df['Data_Status'] == 'Complete']

print(f"Average EPS: ${complete['EPS'].mean():.2f}")
print(f"Average Forward EPS: ${complete['Forward_EPS'].mean():.2f}")
print(f"Average P/E: {complete['PE_Ratio'].mean():.2f}x")
print(f"Average Forward P/E: {complete['Forward_PE'].mean():.2f}x")

print("\nTop 5 by EPS:")
print(complete.nlargest(5, 'EPS')[['Ticker', 'EPS', 'PE_Ratio']])
