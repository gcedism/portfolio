#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime as dt
from datetime import date

from .securities import Securities
from .plotting import basic_plot

class Portfolio:

    def __init__(self, name:str, initial_pricing_date:date, blotters:list[pd.DataFrame]):
        """
        Basic Portfolio Structure 
        :parameters:
            name : str
                String with the name of the portfolio
                
            initial_pricing_date : date
              Pricing date to be used to update prices and other maths
              
            blotters: list, pd.DataFrame
                Two different blotters :
                blotter : pd.DataFrame
                    Trades in different Securities with the structure :
                    date : date of the transaction (datetime date object)
                    id : id of the security
                    quantity : quantity traded (FV / 100 for bonds)
                    cost_price : price paid (received) for the trade
                blotter_cash : pd.DataFrame
                    List of cash movements in the structure : 
                    date : date of the transaction (datetime date object)
                    currency : currency in three letters code
                    amount : amount transfered
                    * each pure FX transaction will be displayed into two lines 
                    representing a credit and a debit transaction
                    ** cash movements from secutiries traded not necessary
                blotter_derivatives : pd.DataFrame
                    To be Implemented
                    
        :methods:
            name : str
                Display the name of the Portfolio
                
            port : pd.DataFrame
                Display the list of all position in the portfolio
                
            assets : pd.DataFrame
                Display the assets Breakdown into :
                    equity - single name equities
                    equities - collective instrument of equity exposure
                    bond - single name of bonds
                    bonds - collective instrument of bonds exposure
                    funds - collective instrument of different exposures
                    cash - cash position
                    
            currencies : pd.DataFrame
                Display the currencies breakdown
                
            cash : pd.DataFrame
                Display the cash position breakdown
                
            bonds : pd.DataFrame
                Display the bonds subportfolio of single lines
                
            equities : pd.DataFrame
                Display the Equities subportfolio of single lines
        
        """
        self._name = name

        self._blotter = self._add_column(blotters['blotter'], 'currency')
        self._cash_blotter = blotters['cash_blotter']

        print('\rUpdating portfolio...', end=' ' * 30, flush=True)
        self.updatePort(initial_pricing_date)

        print('\rUpdating Cash...', end=' ' * 30, flush=True)
        self.updateCash(initial_pricing_date)

        print('\rCalculating Breakdowns...', end=' ' * 30, flush=True)
        self._breakdowns()

        print('\rCalcuating Sub Portfolios...', end=' ' * 30, flush=True)
        self._bonds = Bonds(self.port[self.port['asset_class'] == 'bond']).data
        self._equities = self.port[self.port['asset_class'] == 'equities']
        _options = self.port[self.port['asset_class'] == 'option']
        _options['Option'] = _options.index.map(Securities.options['Option'])
        self._options = Options(_options)
        
        print('\rDone...', end=' ' * 30, flush=True)

    

    def updatePort(self, pricing_dt:date):
        """
        Update Portfolio using pricing_dt as a reference for pricing and calculations
        """

        Securities.update(pricing_dt)
        blotter = self._blotter.loc[self._blotter['date'] <= pricing_dt]
        
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

        A = port.index
        B = Securities.options.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        port.loc[:, 'asset_class'].iloc[c] = 'option'

        self._port = port

    def updateCash(self, pricing_dt:date):
        """
        Update Cash using pricing_dt as a reference for pricing and calculations
        """
        
        Securities.update(pricing_dt)
        cash_blotter = self._cash_blotter.loc[self._cash_blotter['date'] <= pricing_dt]
        blotter = self._blotter.loc[self._blotter['date'] <= pricing_dt]

        blotter['cash_mvmt'] = -blotter['quantity'] * blotter['cost_price'] 
        blotter_cash = blotter.groupby('currency').sum(numeric_only=True)

        cash = cash_blotter.groupby('currency').sum(numeric_only=True)
        cash.loc[:, 'amount'] = cash.loc[:, 'amount'].add(blotter_cash.loc[:, 'cash_mvmt'], fill_value=0)
        cash['ccy_price'] = cash.index.map(Securities.fx['price'])
        cash['mtm'] = cash['amount'] / cash['ccy_price']
        
        self._cash = cash

    def _breakdowns(self):
        """
        Update Breakdowns using current Portfolio
        """
        
        
        if self._port.shape[0] > 0 :
            x = self._port.groupby('currency').sum(numeric_only=True)['mtm'].to_dict()
            y = self._cash['mtm'].to_dict()
            ccy = {k: x.get(k, 0) + y.get(k, 0) for k in set(x) | set(y)}
            
            asset = self._port.groupby('asset_class').sum(numeric_only=True)['mtm'].to_dict()
        else :
            ccy = self._cash['mtm'].to_dict()
            asset = {}
            
        #CURRENCY BREAKDOWN    
        currencies = pd.DataFrame.from_dict(ccy,
                                        orient='index',
                                        columns=['amount'])
        currencies['%'] = currencies['amount'] / currencies['amount'].sum()
        self._currencies = currencies.sort_values(by='%', ascending=False)

        #ASSET BREAKDOWN
        asset['cash'] = self._cash['mtm'].sum()
        assets = pd.DataFrame.from_dict(asset, orient='index', columns=['amount'])
        assets['%'] = assets['amount'] / assets['amount'].sum()
        self._assets = assets

    # Not Working
    # @Basic_plot
    # def print_currencies(*args, **kwargs):
    #   f, ax = plt.subplots(figsize=(5, 5))
    #   ax.pie(self.currencies['%'])
    #   return f, ax

    @staticmethod
    def _add_column(table: pd.DataFrame, column: str) -> pd.DataFrame:
        
        table['eq_aux'] = table.index.map(Securities.equities[column])
        table['fnds_aux'] = table.index.map(Securities.funds[column])
        table['bonds_aux'] = table.index.map(Securities.bonds[column])
        table['options_aux'] = table.index.map(Securities.options[column])
        

        m1 = table['eq_aux'].notna()
        m2 = table['fnds_aux'].notna()
        m3 = table['bonds_aux'].notna()
        m4 = table['options_aux'].notna()

        table[column] = np.select([m1, m2, m3, m4], [table['eq_aux'], table['fnds_aux'], table['bonds_aux'], table['options_aux']], default=np.nan)
        # table.drop(['eq_aux', 'fnds_aux', 'bonds_aux', 'options_aux'], axis=1, inplace=True)

        return table

    @property
    def name(self):
        return self._name
    
    @property
    def port(self):
        return self._port
    
    @property
    def currencies(self):
        display_currencies = self._currencies.style.format({
                    "amount": "{:,.2f}",
                    "%": "{:.2f}"
                    })
        return display_currencies
    
    @property
    def assets(self):
        display_assets = self._assets.style.format({
                    "amount": "{:,.2f}",
                    "%": "{:.2f}"
                    })
        return display_assets
    
    @property
    def bonds(self):
        if isinstance(self._bonds, pd.DataFrame) :
            display_bonds = self._bonds.style.format({
                'maturity' : '{:%y-%m-%d}',
                'qty': '{:,.0f}',
                'mtm': '{:,.0f}',
                'cpn' : '{:,.2f}',
                'price' : '{:,.3f}',
                'yield': '{:.2f}',
                'dur': '{:.1f}',
                'spread': '{:.0f}'
                })
            return display_bonds
        
        else :
            return self._bonds
                
    @property
    def equities(self):
        return self._equities
        
    @property
    def cash(self):
        display_cash = self._cash.style.format({
                    "amount": "{:,.2f}",
                    "ccy_price": "{:,.4f}",
                    "mtm": "{:,.2f}"
                    })
        return display_cash
    
    #To be Used in the Future for calculating performance
    def movements(self, start_date: dt.date, end_date: dt.date):
        blotter = self._blotter[(self.blotter['date'] > start_date)
                           & (self.blotter['date'] <= end_date)]
        blotter = self._add_column(blotter, 'price')
        blotter['ccy_price'] = blotter['currency'].map(Securities.fx['price'])
        blotter['mtm'] = blotter['quantity'] * blotter['price'] / blotter['ccy_price']

        blotter['asset_class'] = blotter.index.map(Securities.funds['asset_class'])
        A = blotter.index
        B = Securities.equities.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        blotter.loc[:, 'asset_class'].iloc[c] = 'equity'
        
        A = blotter.index
        B = Securities.bonds.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        blotter.loc[:, 'asset_class'].iloc[c] = 'bond'
        
        A = blotter.index
        B = Securities.options.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        blotter.loc[:, 'asset_class'].iloc[c] = 'option'

        return blotter.groupby('asset_class').sum(numeric_only=True)


class Bonds:
    """
    Class with a portfolio of Bonds
    :methods :
        data : Displays a DataFrame table with all the info
        avg : Displays the average yield, spread and duration of the portfolio
        
    :To Implement :
        Tables with dv01 per rating/sector/duration
        scenario analyses (with different inputs)
        cash flow projection (adapt from before)
    """

    def __init__(self, bonds: pd.DataFrame):
        """
        Calculate the initial data to be displayed
        :parameters:
            bonds : DataFrame with Bonds position with the structure : 
                id : ISIN Based ID
                quantity : As Face Value / 100
                cost_price : avg clean price of purchase
                price : most recent clean price
                currency : three letters code of currency
                ccy_price : USD / Currency format of price
                mtm : USD market to market value of the position
                asset_class : string with asset class
        """
        if bonds.shape[0] > 0 :
            bonds[['name', 'maturity', 'cpn', 'yield', 'dur', 'spread', 'country', 'sector', 'rating', 'ranking', 'Bond']] = Securities.bonds[['name', 'maturity', 'cpn', 'yield', 'dur', 'spread', 'country', 'sector', 'rating', 'ranking', 'Bond']]
            bonds['aux_yield'] = bonds['mtm'] * bonds['yield']
            bonds['aux_dur'] = bonds['mtm'] * bonds['dur']
        
            self._avg = {
                'yield': bonds['aux_yield'].sum() / bonds['mtm'].sum(),
                'duration': bonds['aux_dur'].sum() / bonds['mtm'].sum()
            }
            bonds = bonds[['name', 'maturity', 'cpn', 'quantity', 'mtm', 'price', 'yield', 'dur', 'spread', 'country', 'sector', 'rating', 'ranking', 'Bond']]
            self._data = bonds.sort_values('maturity')
            
        else :
            self._avg = {}
            self._data = {}

    def cash_projection(self, initial_date: date, end_date: date):

        ints = self.data.apply(lambda x: x['Bond'].cshf.loc[initial_date:end_date] * x['quantity'], axis=1)
        ints = pd.concat([x['flow'] for x in ints]).groupby('dates').sum()
        mats = self.data[(self.data['maturity'] > initial_date)
                     & (self.data['maturity'] <= end_date)].set_index(
                       'maturity').loc[:, 'quantity'] * 100
        mats.index.set_names('dates', inplace=True)
        mats = mats.groupby('dates').sum()

        total_flow = pd.DataFrame(ints)
        total_flow['maturities'] = mats
        total_flow.fillna(0, inplace=True)
        total_flow.loc[:, 'flow'] = total_flow.loc[:, 'flow'] - total_flow.loc[:, 'maturities']
        total_flow = total_flow.groupby('dates').sum()

        return total_flow
    
    @property
    def avg(self):
        return self._avg
    
    @property
    def data(self):
        return self._data

class Options :
    """
    Class with a portfolio of Options for a particular asset
    :methods:
        Net Delta
        Net Gamma 
        Gamma Matrix
        Net vega
        Net Theta
    """
    
    def __init__(self, options:pd.DataFrame) :
        """
        :parameters:
            options : List, Option,
                List of Options
        """
                
        self._table = pd.DataFrame([{'tenor' : round(opt._t, 2),
                                     'c_p' : opt._c_p,
                                     'strike' : opt._K,
                                     'delta' : round(opt.delta, 2),
                                     'vol' : round(opt.vol, 2),
                                     'gamma_up' : round(opt.gamma_up, 2),
                                     'gamma_down' : round(opt.gamma_down, 2),
                                     'vega_up' : round(opt.vega_up, 2),
                                     'vega_down' : round(opt.vega_down, 2),
                                     'theta' : round(opt.theta, 2),
                                    }
                                    for opt in options['Option']]).set_index('tenor')
        self.calc_matrix()
        
    def calc_matrix(self) :
        
        bins = [0, 0.125, 0.375, 0.5, 0.675, 0.875, 1]
        labels =[0.10, 0.25, 0.425, 0.575, 0.75, 0.9]
        self._table['delta_buckets'] = pd.cut(self._table['delta'], bins, labels=labels)
        self._gammaUpMatrix = self._table.pivot_table(values='gamma_up',
                                                      index='delta_buckets',
                                                      columns='tenor',
                                                      aggfunc='sum')
        self._gammaDownMatrix = self._table.pivot_table(values='gamma_down',
                                                        index='delta_buckets',
                                                        columns='tenor',
                                                        aggfunc='sum')
        
    @property
    def table(self) :
        return self._table
        
    @property
    def gammaUpMatrix(self) :
        return self._gammaUpMatrix
    
    @property
    def gammaDownMatrix(self) :
        return self._gammaDownMatrix