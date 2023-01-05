#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime as dt
from datetime import date

from .bond import Bond
from .options import SPYOption

class Securities:
    """
    Main Class that gathers basic information about a list of possible securities
    """

    def __init__(self, AC:list[pd.DataFrame], hist:pd.DataFrame, initial_pricing_dt:date, curves, volatilities) :
        self._pricing_dt = initial_pricing_dt
        self._hist = hist
        self._curves = curves
        self._volatilities = volatilities
        
        self._bonds = AC['bonds']
        self._equities = AC['equities']
        self._funds = AC['funds']
        self._options = AC['options']
        
        self.last_prices()
        self.initial_setup()
        
    def last_prices(self) :
        idx = self._hist.index.get_indexer([self._pricing_dt], method='nearest')
        self._last_prices = self._hist.iloc[idx]
        
    def initial_setup(self) :
        self._bonds['cl_price'] = self._bonds.apply(lambda x: self._last_prices[x.name]
                                         if x.name in self._last_prices.columns else 100,
                                         axis=1)
        self._bonds['Bond'] = self._bonds.apply(lambda x: Bond(x['maturity'], x['cpn'], x['cl_price'], self._curves.zero, self._pricing_dt), axis=1)
        self._bonds[['price', 'yield', 'spread', 'dur']] = self._bonds.apply(lambda x: 
                                                                pd.Series([x['Bond'].price,
                                                                           x['Bond'].y * 100,
                                                                           x['Bond'].spread * 10000,
                                                                           x['Bond'].duration],
                                                                          index=['price', 'yield', 'spread', 'duration']),
                                                                             axis=1)
        
        self._equities['price'] = self._equities.apply(lambda x: self._last_prices[x.name]
                                                   if x.name in self._last_prices.columns else 0, axis=1)
        
        
        self._funds['price'] = self._funds.apply(lambda x: self._last_prices[x.name]
                                             if x.name in self._last_prices.columns else 0, axis=1)
        
        
        self._fx = pd.DataFrame({'id': ['USD', 'EUR', 'CHF', 'CAD', 'BRL', 'GBP'],
                                 'code' : ['USD', 'EUR=X', 'CHF=X', 'CAD=X', 'BRL=X', 'GBP=X']},
                              index=['USD', 'EUR=X', 'CHF=X', 'CAD=X', 'BRL=X', 'GBP=X'])
        
        
        self._fx['price'] = self._fx.apply(lambda x: self._last_prices[x.name][0]
                                       if x.name in self._last_prices.columns else 1, axis=1)
        self._fx.set_index('id', inplace=True)
        
        SPYSpot = self._funds.loc['SPY', 'price']
        self._volatilities.pricing_dt = self._pricing_dt
        self._options['price'] = self._options.apply(lambda x: self._last_prices[x.name]
                                         if x.name in self._hist.columns else 1,
                                         axis=1)
        self._options['Option'] = self._options.apply(lambda x: 
                                                      SPYOption(x.name,
                                                                self._pricing_dt,
                                                                price=x['price'],
                                                                spot=SPYSpot, 
                                                                vol_surface=self._volatilities),
                                                      axis=1)
        
        self._id_all = pd.concat([self._funds[['asset_class', 'currency', 'price']],
                                  self._equities[['asset_class', 'currency', 'price']],
                                  self._bonds[['asset_class', 'currency', 'price']],
                                  self._options[['asset_class', 'currency', 'price']]])
        
    def update(self) :
        self._bonds['cl_price'] = self._bonds.apply(lambda x: self._last_prices[x.name]
                                         if x.name in self._last_prices.columns else 100,
                                         axis=1)
        self._bonds.apply(lambda x: x['Bond'].multiUpdate(self._pricing_dt, x['price'], self._curves.zero), axis=1)
        self._bonds[['cl_price', 'yield', 'spread', 'dur']] = self._bonds.apply(lambda x: 
                                                                pd.Series([x['Bond'],
                                                                           x['Bond'].y * 100,
                                                                           x['Bond'].spread * 10000,
                                                                           x['Bond'].duration],
                                                                          index=['price', 'yield', 'spread', 'duration']), axis=1)
        
        self._equities['price'] = self._equities.apply(lambda x: self._last_prices[x.name]
                                                   if x.name in self._last_prices.columns else 0, axis=1)
                
        self._funds['price'] = self._funds.apply(lambda x: self._last_prices[x.name]
                                             if x.name in self._last_prices.columns else 0, axis=1)
        
        self._fx['price'] = self._fx.apply(lambda x: self._last_prices[x['code']][0]
                                       if x['code'] in self._last_prices.columns else 1, axis=1)
        
        SPYSpot = self._funds.loc['SPY', 'price']
        self._options['price'] = self._options.apply(lambda x: self._last_prices[x.name]
                                         if x.name in self._hist.columns else 1,
                                         axis=1)
        self._options.apply(lambda x: x['Option'].multiUpdate(x['price'], SPYSpot, self._pricing_dt), axis=1)
    
        self._id_all = pd.concat([self._funds[['asset_class', 'currency', 'price']],
                                  self._equities[['asset_class', 'currency', 'price']],
                                  self._bonds[['asset_class', 'currency', 'price']],
                                  self._options[['asset_class', 'currency', 'price']]])
    
    @property
    def bonds(self) :
        return self._bonds
    
    @property
    def equities(self) :
        return self._equities
    
    @property
    def funds(self) :
        return self._funds
    
    @property
    def fx(self) :
        return self._fx
    
    @property
    def options(self) :
        return self._options
    
    @property
    def id_all(self) :
        return self._id_all
    
    @property
    def pricing_dt(self) :
        return self._pricing_dt
    @pricing_dt.setter
    def pricing_dt(self, new_dt:date) :
        self._pricing_dt = new_dt
        self.last_prices()
        self._curves.pricing_dt = new_dt
        self._volatilities.pricing_dt = new_dt
        self.update()        
    
        
        
        
        
        
