import pandas as pd
import matplotlib.pyplot as plt

from Portfolio import Portfolio

from datetime import datetime as dt
from datetime import timedelta as td

pd.set_option('mode.chained_assignment', None)

ACCOUNTS = ['port_1', 'port_2', 'port_3', 'port_4']
pricing_dt = dt.now().date() - td(days=1)

blotters_list = ['blotter', 'cash_blotter']
blotters = {}
for bl in blotters_list:
  blotters[bl] = pd.read_csv('_data/' + bl + '.csv',
                             encoding='UTF-8',
                             index_col=0)
  blotters[bl].loc[:, 'date'] = blotters[bl].loc[:, 'date'].apply(
    lambda x: dt.strptime(x, '%Y-%m-%d').date())

port = Portfolio('Main Portfolio', pricing_dt, blotters)

start = dt(2023, 1, 1).date()
end = dt(2024, 1, 1).date()
print(port.bonds.cash_projection(start, end))

# '{:,.2f}'.format(shared.port.assets['amount'].sum()
