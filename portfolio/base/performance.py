#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.offsetbox import AnchoredText
from datetime import datetime as dt
from datetime import date

from .base import BasePortfolio

# from _bonds import cash_projection
# from _equities import dvd_projection

class Performance(BasePortfolio) :
    
    def movements(self, start_dt:date, end_dt:date) -> pd.DataFrame:
        
        blotter = self._blotter[(self._blotter['date'] > start_dt)
                           & (self._blotter['date'] <= end_dt)]
        blotter = self._add_column(blotter, 'price', self._securities)
        
        #To be fixed with better currency pricing and prices
        blotter['ccy_price'] = blotter['currency'].map(self._securities.fx['price'])
        blotter['mtm'] = blotter['quantity'] * blotter['price'] / blotter['ccy_price']

        blotter['asset_class'] = blotter.index.map(self._securities.funds['asset_class'])
        A = blotter.index
        B = self._securities.equities.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        blotter.loc[:, 'asset_class'].iloc[c] = 'equity'
        
        A = blotter.index
        B = self._securities.bonds.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        blotter.loc[:, 'asset_class'].iloc[c] = 'bond'
        
        A = blotter.index
        B = self._securities.options.index
        c = np.where(pd.Index(pd.unique(B)).get_indexer(A) >= 0)[0]
        blotter.loc[:, 'asset_class'].iloc[c] = 'option'

        return blotter.groupby('asset_class').sum(numeric_only=True)
    
    def cashMovements(self, start_dt:date, end_dt:date) -> pd.DataFrame:
        cash_blotter = (self._cash_blotter.loc[(self._cash_blotter['date'] > start_dt)
                                             & (self._cash_blotter['date'] <= end_dt)]
                        .groupby('currency').sum(numeric_only=True))
        cash_blotter['ccy_price'] = cash_blotter.index.map(self._securities.fx['price'])
        cash_blotter['mtm'] = cash_blotter['amount'] / cash_blotter['ccy_price']
        
        return cash_blotter
        
        
    def historicalPerformance(self, dates:list[date]) -> pd.Series:
        nav = {}
        for certain_date in dates :
            self.pricing_dt = certain_date
            nav[certain_date] = self._assets['amount']
    
        history = pd.DataFrame.from_dict(nav, orient = 'index')
        history['nav'] = history.sum(axis = 1)
        history['perf'] = round( history['nav'] / history['nav'].shift(1) - 1 , 4)
        history['cumPerf'] = round( history['nav'] / history['nav'].iloc[0] -1, 4)
    
        f, ax = plt.subplots(figsize=(12,8))
        
        colors = ['lightblue' if e >= 0 else 'red' for e in history['perf']]
        
        ax.bar(history.index, history['perf'], label = 'perf', color = colors)
        ax2 = ax.twinx()
        ax2.plot(history.index, history['nav'], label = 'NAV', color = 'black')
        
        ax.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        
        ax.legend()
        ax2.legend()
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        
        self.basePort()
        
        return history.loc[:, 'perf']
    
    def performanceAttribution(self, start_dt:date, end_dt:date) :
        self.pricing_dt = start_dt
        values = self._assets

        self.pricing_dt = end_dt
        values['endAmt'] = self._assets['amount']

        mvmts = self.movements(start_dt, end_dt).groupby('asset_class').sum()['mtm']

        values['adjEndAmt'] = pd.Series({x: values.loc[x, 'endAmt']-mvmts[x] if (x in mvmts.index) else values.loc[x, 'endAmt'] for x in values.index})
        values.loc['cash', 'adjEndAmt'] = values.loc['cash', 'endAmt'] + mvmts.sum()
        values['perf'] = values['adjEndAmt'] / values['amount'] - 1
        values['perfAttr'] = values['perf'] * values['%']
    
        values = self.transformValues(values)
        self.printValues(values, start_dt, end_dt)
        
        self.basePort()
        
    def performanceAttribution2(self, start_dt:date, end_dt:date) :
        self.pricing_dt = end_dt
        table = self._assets

        self.pricing_dt = start_dt
        table['start_amt'] = self._assets['amount']
        
        try :
            table['mvmts'] = self.movements(start_dt, end_dt)['mtm']
        except :
            table['mvmts'] = [0] * table.shape[0]
        
        try :
            cash_mvmts = self.cashMovements(start_dt, end_dt)['mtm'].sum()
        except : 
            cash_mvmts = 0
        table.loc['cash', 'mvmts'] = - table['mvmts'].sum() + cash_mvmts
        
        table.fillna(0, inplace=True)
        table['pnl'] = table['amount'] - table['mvmts'] - table['start_amt']
        table['perf'] = table['pnl'] / table['start_amt']
        table['perfAttr'] = table['perf'] * table['%']
        table.replace([np.inf, -np.inf], 0, inplace=True)
        
        self.basePort()
        
        return table

    def transformValues(self, values) : 
        values['absPerfAttr'] = abs(values['perfAttr'])
        values.sort_values('absPerfAttr', ascending = False, inplace = True)
        values['cumPerfAttr'] = values['perfAttr'].cumsum()
    
        values['b_graph1'] = values['perfAttr']
        values['t_graph1'] = values['perfAttr']
        values['color1'] = values['perfAttr']
        values['t_graph2'] = values['perfAttr']
        values['color2'] = values['perfAttr']

        values.loc[values.index[0], 'b_graph1'] = 0
        values.loc[values.index[0], 't_graph1'] = 0
        values.loc[values.index[0], 'color1'] = 'w'
        values.loc[values.index[0], 't_graph2'] = values.iloc[0]['cumPerfAttr']
        if values.iloc[0]['cumPerfAttr'] >= 0 :
            values.loc[values.index[0], 'color2'] = 'b'
        else :
            values.loc[values.index[0], 'color2'] = 'r'

        for i in range(1, values.shape[0]) : 
            next_v = values.iloc[i]['perfAttr']
    
            if  values.iloc[i-1]['cumPerfAttr'] >= 0 :
                if next_v >=0 :
                    values.loc[values.index[i], 'b_graph1'] = 0
                    values.loc[values.index[i], 't_graph1'] = values.iloc[i-1]['cumPerfAttr']
                    values.loc[values.index[i], 'color1'] = 'w'
                    values.loc[values.index[i], 't_graph2'] = next_v
                    values.loc[values.index[i], 'color2'] = 'b'
                    
                else :
                    if values.iloc[i]['cumPerfAttr'] >= 0 :
                        values.loc[values.index[i], 'b_graph1'] = 0
                        values.loc[values.index[i], 't_graph1'] = values.iloc[i]['cumPerfAttr']
                        values.loc[values.index[i], 'color1'] = 'w'
                        values.loc[values.index[i], 't_graph2'] = abs(next_v)
                        values.loc[values.index[i], 'color2'] = 'r'
                    else :
                        values.loc[values.index[i], 'b_graph1'] = 0
                        values.loc[values.index[i], 't_graph1'] = 0
                        values.loc[values.index[i], 'color1'] = 'w'
                        values.loc[values.index[i], 't_graph2'] = next_v + values.iloc[i-1]['cumPerfAttr']
                        values.loc[values.index[i], 'color2'] = 'r'
            else :
                if next_v < 0 :
                    values.loc[values.index[i], 'b_graph1'] = 0
                    values.loc[values.index[i], 't_graph1'] = values.iloc[i-1]['cumPerfAttr']
                    values.loc[values.index[i], 'color1'] = 'w'
                    values.loc[values.index[i], 't_graph2'] = next_v
                    values.loc[values.index[i], 'color2'] = 'r'
                    
                else :
                    if values.iloc[i]['cumPerfAttr'] < 0 :
                        values.loc[values.index[i], 'b_graph1'] = 0
                        values.loc[values.index[i], 't_graph1'] = values.iloc[i]['cumPerfAttr']
                        values.loc[values.index[i], 'color1'] = 'w'
                        values.loc[values.index[i], 't_graph2'] = - next_v
                        values.loc[values.index[i], 'color2'] = 'b'
                    else :
                        values.loc[values.index[i], 'b_graph1'] = 0
                        values.loc[values.index[i], 't_graph1'] = 0
                        values.loc[values.index[i], 'color1'] = 'w'
                        values.loc[values.index[i], 't_graph2'] = next_v + values.iloc[i-1]['cumPerfAttr']
                        values.loc[values.index[i], 'color2'] = 'b'
                

        values.loc['Total'] = values.sum()
        values.loc['Total', 'b_graph1'] = 0
        values.loc['Total', 't_graph1'] = 0
        values.loc['Total', 'color1'] = 'w'
        values.loc['Total', 't_graph2'] = values.loc['Total', 'perfAttr']
        if values.loc['Total', 'perfAttr'] >= 0 :
            values.loc['Total', 'color2'] = 'black'
        else : 
            values.loc['Total', 'color2'] = 'red'
        
        return values
    
    def printValues(self, values, start_dt, end_dt) : 
        f, ax = plt.subplots(figsize=(12, 8))
        sDate = dt.strftime(start_dt, '%d-%b-%y')
        eDate = dt.strftime(end_dt, '%d-%b-%y')
        f.suptitle(f'Performance Attribution\nFrom {sDate} to {eDate}', fontsize = 16, fontweight = 'bold')

        ax.bar(values.index, values['t_graph1'] * 100, bottom = values['b_graph1'] * 100, color = values['color1'], label = 'Perf Attribution')
        ax.bar(values.index, values['t_graph2'] * 100, bottom = values['t_graph1'] * 100, color = values['color2'], label = 'Perf Attribution')
        for k in range(values.shape[0] - 1) :
            ax.plot([values.index[k], values.index[k+1]], 
            [values.loc[values.index[k], 'cumPerfAttr'] * 100, values.loc[values.index[k], 'cumPerfAttr'] * 100],
            color = 'grey', ls = 'dotted') 
    
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.spines[['right', 'top']].set_visible(False)
        
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
    
    def cashFlowProjection(self, start_dt, end_dt) :
        all_cash = self._bonds.cash_projection(start_dt, end_dt)
        # dvds = dvd_projection(shared.port.equities, initial_date, end_date)
        # all_cash = pd.concat([interests, dvds])
        all_cash['month'] = [k.strftime('%y-%m') for k in all_cash.index]
        all_cash = all_cash.groupby('month').sum()
        all_cash.index = [dt.strptime(k, '%y-%m').strftime('%b-%y') for k in all_cash.index]
        
        f, ax = plt.subplots(figsize = (12,8))
        f.suptitle(f'Cash Flow expected\nFrom {start_dt} to {end_dt}', fontsize = 16, fontweight = 'bold')

        ax.bar(all_cash.index, all_cash['flow'], color = 'b', label = 'Interests and Dividends')
        ax.bar(all_cash.index, all_cash['maturities'], color = 'yellow', alpha = 0.5, label = 'maturities')

        text = f"Total = {format(all_cash['flow'].sum(), ',.0f')}"
        props = dict(size=16, color = 'red')
        params = {
            's' : text,
            'frameon' : False,
            'borderpad' : 0,
            'pad' : 0.1, 
            'loc' : 'center right',
            'bbox_transform' : plt.gca().transAxes,
            'prop' : props}
        total = AnchoredText(**params)
        ax.add_artist(total)

        height = 2000 if sum(all_cash['maturities']) > 0 else 100
        params = {'color' : 'black',
                'fontsize' : 12,
                'verticalalignment':'top',
                 'ha': 'center'}
        all_cash.apply(lambda x : ax.text(x.name, x['flow'] + height, format(x['flow'], ',.0f'), **params), axis = 1)

        ax.spines[['right', 'top']].set_visible(False)
        
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)

        plt.legend()
    
    