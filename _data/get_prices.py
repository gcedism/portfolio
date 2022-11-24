import pandas as pd
import yfinance as yf
from datetime import datetime as dt

FOLDER = __file__[:-len('get_prices.py')]

equities = pd.read_csv(FOLDER + 'equities.csv', index_col=0).index.tolist()
funds = pd.read_csv(FOLDER + 'funds.csv', index_col=0).index.tolist()
fx = ['EUR=X', 'CHF=X', 'CAD=X', 'BRL=X', 'GBP=X']
ytickers = equities + funds + fx

y_hist = yf.download(ytickers, period='1y', interval='1d')['Adj Close']
y_hist.index = y_hist.index.map(lambda x: x.date())

bonds_hist = pd.read_csv(FOLDER + 'bonds_prices.csv', index_col=0)
bonds_hist.index = bonds_hist.index.map(
  lambda x: dt.strptime(x, '%Y-%m-%d').date())

hist = bonds_hist.join(y_hist, how='outer')
