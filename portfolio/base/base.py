#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime as dt
from datetime import date

from ..utils.utils import interpolate

class BasePortfolio:

    def __init__(self, name:str, initial_pricing_date:date, blotters:list[pd.DataFrame], securities):
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
        self._basePricing_dt = initial_pricing_date
        self._pricing_dt = initial_pricing_date
        self._securities = securities

        self._blotter = self._add_column(blotters['blotter'], 'currency', self._securities)
        self._cash_blotter = blotters['cash_blotter']

        print('\rUpdating portfolio...', flush=True)
        self.basePort()

        print('\rCalcuating Sub Portfolios...', flush=True)
        self._bonds = Bonds(self._port[self._port['asset_class'] == 'bond'], self._securities)
        self._equities = self._port[self.port['asset_class'] == 'equities']
        _options = self._port[self.port['asset_class'] == 'options']
        if not _options.empty :
            _options['Option'] = _options.index.map(self._securities.options['Option'])
            self._options = Options(_options, self._securities)
        
        print('\rDone...', flush=True)
        
    def totalUpdate(self) :
        self.updatePort()
        self.updateCash()
        self._breakdowns()
    
    def basePort(self) :
        self._pricing_dt = self._basePricing_dt
        self._securities.pricing_dt = self._basePricing_dt
        self.totalUpdate()
    
    def updatePort(self) :
        """
        Update Portfolio using pricing_dt as a reference for pricing and calculations
        """
        blotter = self._blotter.loc[self._blotter['date'] <= self._pricing_dt]
        blotter['auxPrice'] = blotter['cost_price'] * blotter['quantity']
        port = blotter.groupby('id').sum(numeric_only=True)
        port['cost_price'] = port['auxPrice'] / port['quantity']
        
        port['asset_class'] = port.index.map(self._securities.id_all['asset_class'])
        port['price'] = port.index.map(self._securities.id_all['price'])
        port['currency'] = port.index.map(self._securities.id_all['currency'])
        port['ccy_price'] = port['currency'].map(self._securities.fx['price'])
        
        port['mtm'] = port['quantity'] * port['price'] / port['ccy_price']
        
        self._port = port[['quantity', 'cost_price', 'price', 'currency',  'ccy_price', 'mtm', 'asset_class']]
                
    def updateCash(self):
        """
        Update Cash using pricing_dt as a reference for pricing and calculations
        """
        cash_blotter = self._cash_blotter.loc[self._cash_blotter['date'] <= self._pricing_dt]
        blotter = self._blotter.loc[self._blotter['date'] <= self._pricing_dt]

        blotter['cash_mvmt'] = -blotter['quantity'] * blotter['cost_price'] 
        blotter_cash = blotter.groupby('currency').sum(numeric_only=True)

        cash = cash_blotter.groupby('currency').sum(numeric_only=True)
        cash.loc[:, 'amount'] = cash.loc[:, 'amount'].add(blotter_cash.loc[:, 'cash_mvmt'], fill_value=0)
        cash['ccy_price'] = cash.index.map(self._securities.fx['price'])
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

    @property
    def pricing_dt(self) :
        return self._pricing_dt
    @pricing_dt.setter
    def pricing_dt(self, new_dt:date):
        self._pricing_dt = new_dt
        self._securities.pricing_dt = new_dt
        self.totalUpdate()
        
    @staticmethod
    def _add_column(table: pd.DataFrame, column: str, securities) -> pd.DataFrame:
        
        table['eq_aux'] = table.index.map(securities.equities[column])
        table['fnds_aux'] = table.index.map(securities.funds[column])
        table['bonds_aux'] = table.index.map(securities.bonds[column])
        table['options_aux'] = table.index.map(securities.options[column])
        

        m1 = table['eq_aux'].notna()
        m2 = table['fnds_aux'].notna()
        m3 = table['bonds_aux'].notna()
        m4 = table['options_aux'].notna()

        table[column] = np.select([m1, m2, m3, m4], [table['eq_aux'], table['fnds_aux'], table['bonds_aux'], table['options_aux']], default=np.nan)
        # table.drop(['eq_aux', 'fnds_aux', 'bonds_aux', 'options_aux'], axis=1, inplace=True)

        return table

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

    def __init__(self, bonds: pd.DataFrame, securities):
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
        self._securities = securities
        if bonds.shape[0] > 0 :
            bonds[['name', 'maturity', 'cpn', 'yield', 'dur', 'spread', 'country', 'sector', 'rating', 'ranking', 'Bond']] = self._securities.bonds[['name', 'maturity', 'cpn', 'yield', 'dur', 'spread', 'country', 'sector', 'rating', 'ranking', 'Bond']]
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

    def cash_projection(self, start_dt:date, end_dt:date) -> pd.DataFrame:

        ints = self._data.apply(lambda x: x['Bond'].cshf.loc[start_dt:end_dt] * x['quantity'], axis=1)
        ints = pd.concat([x['flow'] for x in ints]).groupby('dates').sum()
        mats = self._data[(self._data['maturity'] > start_dt)
                     & (self._data['maturity'] <= end_dt)].set_index(
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
    
    def __init__(self, options:pd.DataFrame, securities) :
        """
        :parameters:
            options : pd.DataFrame, Option,
                List of Options
        """
        
        self._spot = options['Option'][0].spot
        self._options = options
        self._securities = securities
        self.expandDetails()
        
    def expandDetails(self):
        self._options[['price', 'tenor', 'c_p', 'strike', 'delta', 'delta$', 'vol',
                       'gamma_up', 'gamma_down', 'vega_up', 'vega_down', 'theta']
                     ] = self._options.apply(lambda x: pd.Series(
            [x['Option'].price,
             x['Option']._t, x['Option']._c_p, x['Option']._K,
             x['Option'].delta,
             x['Option'].delta * x['Option'].spot * x['quantity'] * x['ccy_price'],
             x['Option'].vol,
             x['Option'].gamma_up * x['Option'].spot * x['quantity'] * x['ccy_price'],
             x['Option'].gamma_down * x['Option'].spot * x['quantity'] * x['ccy_price'],
             x['Option'].vega_up * x['quantity'],
             x['Option'].vega_down * x['quantity'],
             x['Option'].theta * x['quantity']],
            index=['price', 'tenor', 'c_p', 'strike', 'delta', 'delta$', 'vol',
                   'gamma_up', 'gamma_down', 'vega_up',
                   'vega_down', 'theta']), axis =1)
            
        self._options['mtm'] = self._options['quantity'] * self._options['price']
        
        self._totalGamma = (self._options['gamma_up'].sum() + self._options['gamma_down'].sum())/ 2
        self._totalDelta = self._options['delta$'].sum()
        self._totalTheta = self._options['theta'].sum()
        self._mtm = self._options['mtm'].sum()
        self.calc_matrix()
    
    def updatePrices(self, prices:dict) :
        self._options['price'] = self._options.index.map(prices)
        for opt, p in zip(self._options['Option'], self._options['price']) :
            opt.price = p
    
    def updateSpot(self, spot) :
        r = 0.04
        i = 0.02
        pricing_dt = date(2022, 12, 19) # Careful with that, to be changed in the future
        # vol_c = vol_curve(pricing_dt, r, i) 
        for opt in self._options['Option'] :
            opt.spot = spot
            opt.vol = interpolate((opt._t, opt._K), vol_c)
        
        self.expandDetails()
        
    
    def calc_matrix(self) :
        
        bins = np.array([0.5, 0.8625, 0.925, 0.975, 1.025, 1.075, 1.1375, 1.3375]) * self._spot
        labels =['-OTM', '-13.75%', '-7.5%', 'ATM', '+7.5%', '+13.75%', '+OTM']
        self._options['moneyness'] = pd.cut(self._options['strike'], bins, labels=labels)
        self._gammaUpMatrix = self._options.pivot_table(values='gamma_up',
                                                      index='moneyness',
                                                      columns='tenor',
                                                      aggfunc='sum')
        self._gammaDownMatrix = self._options.pivot_table(values='gamma_down',
                                                        index='moneyness',
                                                        columns='tenor',
                                                        aggfunc='sum')
        
    @property
    def gammaUpMatrix(self) :
        return self._gammaUpMatrix
    
    @property
    def gammaDownMatrix(self) :
        return self._gammaDownMatrix