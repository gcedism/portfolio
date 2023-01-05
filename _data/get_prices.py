import pandas as pd
import yfinance as yf
from datetime import datetime as dt

equities = pd.read_csv('_data/equities.csv', index_col=0).index.tolist()
funds = pd.read_csv('_data/funds.csv', index_col=0).index.tolist()
options = pd.read_csv('_data/options.csv', index_col=0).index.tolist()
fx = ['EUR=X', 'CHF=X', 'CAD=X', 'BRL=X', 'GBP=X']
not_yahoo = ['CRYPTO']
ytickers = [x for x in (equities + funds + fx + options) if x not in not_yahoo]

y_hist = yf.download(ytickers, period='1y', interval='1d')['Adj Close']
y_hist.index = y_hist.index.map(lambda x: x.date())

bonds_hist = pd.read_csv('_data/bonds_prices.csv', index_col=0)
bonds_hist.index = bonds_hist.index.map(
  lambda x: dt.strptime(x, '%d.%m.%y').date())

hist = bonds_hist.join(y_hist, how='outer')

