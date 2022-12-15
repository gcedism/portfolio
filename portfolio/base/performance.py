#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import date

from .base import BasePortfolio

class Performance(BasePortfolio) :
    
    #To be Used in the Future for calculating performance
    def movements(self, start_date: date, end_date: date):
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
    
    