import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime as dt
from .securities import Securities
from .plotting import basic_plot


class Portfolio:

  def __init__(self, name: str, initial_pricing_date, blotters):
    '''
    Basic Portfolio Structure 
      name : string with the name of the portfolio
      initial_pricing_date : datetime date object
      blotters: list with two different blotters :
        blotter : DataFrame with trades in different Securities with the structure :
          date : date of the transaction (datetime date object)
          id : id of the security
          quantity : quantity traded (FV / 100 for bonds)
          cost_price : price paid (received) for the trade
        blotter_cash : DataFrame with list of cash movements in the structure : 
          date : date of the transaction (datetime date object)
          currency : currency in three letters code
          amount : amount transfered
          * each pure FX transaction will be displayed into two lines 
          representing a credit and a debit transaction
          ** cash movements from secutiries traded not necessary
        blotter_derivatives :
          To be Implemented
    '''
    self._name = name

    self.blotter = self._add_column(blotters['blotter'], 'currency')
    self.cash_blotter = blotters['cash_blotter']

    print('\rUpdating portfolio...', end=' ' * 30, flush=True)
    self.updatePort(initial_pricing_date)

    print('\rUpdating Cash...', end=' ' * 30, flush=True)
    self.updateCash(initial_pricing_date)

    print('\rCalculating Breakdowns...', end=' ' * 30, flush=True)
    self._breakdowns()

    print('\rCalcuating Sub Portfolios...', end=' ' * 30, flush=True)
    self.bonds = bonds(self.port[self.port['asset_class'] == 'bond'])
    self.equities = self.port[self.port['asset_class'] == 'equities']

    print('\rDone...', end=' ' * 30, flush=True)

  def movements(self, start_date: dt.date, end_date: dt.date):
    blotter = self.blotter[(self.blotter['date'] > start_date)
                           & (self.blotter['date'] <= end_date)]
    blotter = self._add_column(blotter, 'price')
    blotter['ccy_price'] = blotter['currency'].map(self.Securities.fx['price'])
    blotter[
      'mtm'] = blotter['quantity'] * blotter['price'] / blotter['ccy_price']

    blotter['asset_class'] = blotter.index.map(Securities.funds['asset_class'])
    A = blotter.index
    B = Securities.equities.index
    c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
    blotter.loc[:, 'asset_class'].iloc[c] = 'equity'
    A = blotter.index
    B = Securities.bonds.index
    c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
    blotter.loc[:, 'asset_class'].iloc[c] = 'bond'

    return blotter.groupby('asset_class').sum(numeric_only=True)

  def updatePort(self, pricing_dt):
    Securities.update(pricing_dt)
    blotter = self.blotter[self.blotter['date'] <= pricing_dt]

    port = blotter.groupby('id').sum(numeric_only=True)
    port = self._add_column(port, 'price')
    port = self._add_column(port, 'currency')
    port = port[['quantity', 'cost_price', 'price', 'currency']]
    port['ccy_price'] = port['currency'].map(Securities.fx['price'])
    port['mtm'] = port['quantity'] * port['price'] / port['ccy_price']
    port['asset_class'] = port.index.map(Securities.funds['asset_class'])

    A = port.index
    B = Securities.equities.index
    c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
    port.loc[:, 'asset_class'].iloc[c] = 'equity'

    A = port.index
    B = Securities.bonds.index
    c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
    port.loc[:, 'asset_class'].iloc[c] = 'bond'

    # A = port.index
    # B = options.index
    # c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
    # port.loc[:, 'asset_class'].iloc[c] = 'option'

    self.port = port

  def updateCash(self, pricing_dt):
    Securities.update(pricing_dt)
    cash_blotter = self.cash_blotter[self.cash_blotter['date'] <= pricing_dt]
    blotter = self.blotter[self.blotter['date'] <= pricing_dt]

    blotter['ccy_price'] = blotter['currency'].map(Securities.fx['price'])
    blotter['cash_mvmt'] = -blotter['quantity'] * blotter[
      'cost_price'] / blotter['ccy_price']
    blotter_cash = blotter.groupby('currency').sum(numeric_only=True)

    cash = cash_blotter.groupby('currency').sum(numeric_only=True)
    cash['ccy_price'] = cash.index.map(Securities.fx['price'])
    cash['mtm'] = cash['amount'] / cash['ccy_price']

    self.cash = cash['mtm'].add(blotter_cash['cash_mvmt'], fill_value=0)

  def _breakdowns(self):
    #CURRENCY BREAKDOWN
    x = self.port.groupby('currency').sum(numeric_only=True)['mtm'].to_dict()
    y = self.cash.to_dict()
    ccy = {k: x.get(k, 0) + y.get(k, 0) for k in set(x) | set(y)}
    currencies = pd.DataFrame.from_dict(ccy,
                                        orient='index',
                                        columns=['amount'])
    currencies['%'] = currencies['amount'] / currencies['amount'].sum()
    self.currencies = currencies.sort_values(by='%', ascending=False)

    #ASSET BREAKDOWN
    asset = self.port.groupby('asset_class').sum(
      numeric_only=True)['mtm'].to_dict()
    asset['cash'] = self.cash.sum()
    assets = pd.DataFrame.from_dict(asset, orient='index', columns=['amount'])
    assets['%'] = assets['amount'] / assets['amount'].sum()
    self.assets = assets

  # Not Working
  # @Basic_plot
  # def print_currencies(*args, **kwargs):
  #   f, ax = plt.subplots(figsize=(5, 5))
  #   ax.pie(self.currencies['%'])
  #   return f, ax

  @staticmethod
  def _add_column(table, column):
    table['eq_aux'] = table.index.map(Securities.equities[column])
    table['fnds_aux'] = table.index.map(Securities.funds[column])
    table['bonds_aux'] = table.index.map(Securities.bonds[column])

    m1 = table['eq_aux'].notna()
    m2 = table['fnds_aux'].notna()
    m3 = table['bonds_aux'].notna()

    table[column] = np.select(
      [m1, m2, m3], [table['eq_aux'], table['fnds_aux'], table['bonds_aux']],
      default=np.nan)
    table.drop(['eq_aux', 'fnds_aux', 'bonds_aux'], axis=1, inplace=True)

    return table

  @property
  def name(self):
    return self._name


class bonds:
  '''
  Class with a portfolio of Bonds
  methods :
  - data : Displays a DataFrame table with all the info
  - avg : Displays the average yield, spread and duration of the portfolio
  - To Implement :
    - Tables with dv01 per rating/sector/duration
    - scenario analyses (with different inputs)
    - cash flow projection (adapt from before)
  '''

  def __init__(self, bonds: pd.DataFrame):
    '''
    Calculate the initial data to be displayed
      bonds : DataFrame with Bonds position with the structure : 
        id : ISIN Based ID
        quantity : As Face Value / 100
        cost_price : avg clean price of purchase
        price : most recent clean price
        currency : three letters code of currency
        ccy_price : USD / Currency format of price
        mtm : USD market to market value of the position
        asset_class : string with asset class
    '''
    bonds[[
      'name', 'maturity', 'cpn', 'yield', 'dur', 'spread', 'country', 'sector',
      'rating', 'ranking', 'Bond'
    ]] = Securities.bonds[[
      'name', 'maturity', 'cpn', 'yield', 'dur', 'spread', 'country', 'sector',
      'rating', 'ranking', 'Bond'
    ]]
    bonds['aux_yield'] = bonds['mtm'] * bonds['yield']
    bonds['aux_dur'] = bonds['mtm'] * bonds['dur']
    self.avg = {
      'yield': bonds['aux_yield'].sum() / bonds['mtm'].sum(),
      'duration': bonds['aux_dur'].sum() / bonds['mtm'].sum()
    }
    bonds = bonds[[
      'name', 'maturity', 'cpn', 'quantity', 'mtm', 'price', 'yield', 'dur',
      'spread', 'country', 'sector', 'rating', 'ranking', 'Bond'
    ]]
    self.data = bonds.sort_values('maturity')

  def cash_projection(self, initial_date: dt.date, end_date: dt.date):

    ints = self.data.apply(
      lambda x: x['Bond'].cshf.loc[initial_date:end_date] * x['quantity'],
      axis=1)
    ints = pd.concat([x['flow'] for x in ints]).groupby('dates').sum()
    mats = self.data[(self.data['maturity'] > initial_date)
                     & (self.data['maturity'] <= end_date)].set_index(
                       'maturity').loc[:, 'quantity'] * 100
    mats.index.set_names('dates', inplace=True)
    mats = mats.groupby('dates').sum()

    total_flow = pd.DataFrame(ints)
    total_flow['maturities'] = mats
    total_flow.fillna(0, inplace=True)
    total_flow.loc[:,
                   'flow'] = total_flow.loc[:,
                                            'flow'] - total_flow.loc[:,
                                                                     'maturities']
    total_flow = total_flow.groupby('dates').sum()

    return total_flow
