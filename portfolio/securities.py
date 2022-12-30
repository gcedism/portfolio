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
        self._hist = hist
        self._pricing_dt = initial_pricing_dt
        self._bonds = AC['bonds']
        self._equities = AC['equities']
        self._funds = AC['funds']
        self._options = AC['options']
        self._curves = curves
        self._volatilities = volatilities
        
        self.update()
    
    def update(self) :
        self._bonds['price'] = self._bonds.apply(lambda x: self._hist.loc[self._pricing_dt, x.name]
                                         if x.name in self._hist.columns else 100,
                                         axis=1)
        self._bonds['Bond'] = self._bonds.apply(lambda x: Bond(x['maturity'], x['cpn'], x['price'], self._curves.zero, self._pricing_dt), axis=1)
        self._bonds[['yield', 'spread', 'dur']] = self._bonds.apply(lambda x: 
                                                                pd.Series([x['Bond'].y * 100,
                                                                           x['Bond'].spread * 10000,
                                                                           x['Bond'].duration],
                                                                          index=['yield', 'spread', 'duration']), axis=1)
        self._equities['price'] = self._equities.apply(lambda x: self._hist.loc[self._pricing_dt, x.name]
                                                   if x.name in self._hist.columns else 0, axis=1)
        
        
        self._funds['price'] = self._funds.apply(lambda x: self._hist.loc[self._pricing_dt, x.name]
                                             if x.name in self._hist.columns else 0, axis=1)
        
        
        self._fx = pd.DataFrame({'id': ['USD', 'EUR', 'CHF', 'CAD', 'BRL', 'GBP']},
                              index=['USD', 'EUR=X', 'CHF=X', 'CAD=X', 'BRL=X', 'GBP=X'])
        
        
        self._fx['price'] = self._fx.apply(lambda x: self._hist.loc[self._pricing_dt, x.name]
                                       if x.name in self._hist.columns else 1, axis=1)
        self._fx.set_index('id', inplace=True)
        
        
        self._volatilities.pricing_dt = self._pricing_dt
        self._options['price'] = self._options.apply(lambda x: self._hist.loc[self._pricing_dt, x.name]
                                         if x.name in self._hist.columns else 1,
                                         axis=1)
        self._options['Option'] = self._options.apply(lambda x: 
                                                      SPYOption(x.name,
                                                                self._pricing_dt,
                                                                price=x['price'],
                                                                vol_surface=self._volatilities),
                                                      axis=1)
        
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
    def pricing_dt(self) :
        return self._pricing_dt
    @pricing_dt.setter
    def pricing_dt(self, new_dt:date) :
        self._pricing_dt = new_dt
        self._curves.pricing_dt = new_dt
        self._volatilities.pricing_dt = new_dt
        self.update()        
    
        
        
        
        
        
