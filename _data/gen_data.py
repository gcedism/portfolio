import pandas as pd
from datetime import datetime as dt


def gen_cash_blotter():
  mvmts = [{
    'currency': 'USD',
    'date': '2022-1-01',
    'amount': 1_000_000,
    'portfolio': 'port_1'
  }, {
    'currency': 'EUR',
    'date': '2022-1-01',
    'amount': 1_000_000,
    'portfolio': 'port_1'
  }]
  pd.DataFrame(mvmts).set_index('currency').to_csv('_data/cash_blotter.csv')


def translate_data():
  _df = pd.read_csv('_data/blotter.csv', index_col=0)
  _df['date'] = _df['date'].map(lambda x: dt.strptime(x, '%d.%m.%y').date())
  _df.to_csv('_data/blotter.csv')
