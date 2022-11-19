import pandas as pd
from pandas.tseries.offsets import CDay
import portfolio as pf

from datetime import datetime as dt
from datetime import timedelta as td

pd.set_option('mode.chained_assignment', None)
'''
Main Procedure to gatter necessary data and create a portfolio
Blotters : 
  blotter : csv File with the following structure
    date : date of the transaction (Y-m-d format)
    id : id of the security
    quantity : quantity traded (FV / 100 for bonds)
    cost_price : price paid (received) for the trade
    account : string to specific account managed
  blotter_cash : DataFrame with list of cash movements in the structure : 
    date : date of the transaction (Y-m-d format)
    currency : currency in three letters code
    amount : amount transfered
    account : string to specific account managed
    * each pure FX transaction will be displayed into two lines 
    representing a credit and a debit transaction
    ** cash movements from secutiries traded not necessary
  blotter_derivatives :
    To be Implemented
'''

ACCOUNTS = ['port_1', 'port_2', 'port_3', 'port_4']
sel_acc = ACCOUNTS
pricing_dt = (dt.now() - CDay(1)).date()

blotters_list = ['blotter', 'cash_blotter']
blotters = {}
for bl in blotters_list:
  blotters[bl] = pd.read_csv('_data/' + bl + '.csv',
                             encoding='UTF-8',
                             index_col=0)
  blotters[bl].loc[:, 'date'] = blotters[bl].loc[:, 'date'].apply(
    lambda x: dt.strptime(x, '%Y-%m-%d').date())
  blotters[bl] = blotters[bl][blotters[bl]['account'].isin(sel_acc)]

port = pf.portfolio('Main Portfolio', pricing_dt, blotters)

start = dt(2023, 1, 1).date()
end = dt(2024, 1, 1).date()
print(port.bonds.data)

# '{:,.2f}'.format(shared.port.assets['amount'].sum()
