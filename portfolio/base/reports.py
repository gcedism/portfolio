#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from IPython.display import display_html
from datetime import datetime as dt
from datetime import date
from pandas.tseries.offsets import CDay

from .base import BasePortfolio

FOLDER = __file__[:-len('base/reports.py')]

class Reports(BasePortfolio) :
    
    def OptionsReport(self, period:str='mtd') :
        
        if period == 'mtd' :
            mtd_date = (date(self._basePricing_dt.year, self._basePricing_dt.month, 1) - CDay(1)).date()
            self.pricing_dt = mtd_date
            try :
                _totalMtm_Mtd = self._assets['amount'].sum()
            except :
                print('No assets')
                _totalMtm_Mtd = 0
            
            self.basePort()
            try :
                _cashMvmts = self.cashMovements(mtd_date, self._basePricing_dt)['amount'].sum()
            except : 
                print('No Cash Mvmt')
                _cashMvmts = 0
            
        
        _date = format(dt.now(), '%Y-%b-%d %H:%M')
        _portDelta = 0
        if 'equity' in self._assets.index :
            _portDelta += self._assets.loc['equity', 'amount']
        if 'equities' in self._assets.index :
            _portDelta += self._assets.loc['equities', 'amount']
        if 'multi-asset' in self._assets.index :
            _portDelta += self._assets.loc['multi-asset', 'amount'] / 2
            
        _totalDelta = _portDelta + self._options._totalDelta
        _totalMtm = self._assets['amount'].sum()
        _totalDeltaPer = _totalDelta / _totalMtm 
        _pnl = _totalMtm - _cashMvmts - _totalMtm_Mtd 
        _gammaUpMatrix = self._options.gammaUpMatrix.copy()
        _gammaUpMatrix.columns = np.round(_gammaUpMatrix.columns, 2).astype(str)
        _gammaDownMatrix = self._options.gammaDownMatrix.copy()
        _gammaDownMatrix.columns = np.round(_gammaDownMatrix.columns, 2).astype(str)
        
        tpl = ""
        with open(FOLDER + 'reports/options.html') as f:
            tpl = f.read()
            f.close()
        
        tpl = tpl.replace('{{date}}', _date)
        tpl = tpl.replace('{{period}}', period)
        
        tpl = tpl.replace('{{optionsDelta}}', "{:,.0f}".format(self._options._totalDelta))
        tpl = tpl.replace('{{portDelta}}', "{:,.0f}".format(_portDelta))
        tpl = tpl.replace('{{totalDelta$}}', "{:,.0f}".format(_totalDelta))
        tpl = tpl.replace('{{totalDelta%}}', "{:.2%}".format(_totalDeltaPer))
        
        tpl = tpl.replace('{{gamma}}', "{:,.0f}".format(self._options._totalGamma))
        tpl = tpl.replace('{{theta}}', "{:,.0f}".format(self._options._totalTheta))
                
        tpl = tpl.replace('{{mtm}}', "{:,.0f}".format(_totalMtm))
        tpl = tpl.replace('{{mtm_mtd}}', "{:,.0f}".format(_totalMtm_Mtd))
        tpl = tpl.replace('{{cashMvmts}}', "{:,.0f}".format(_cashMvmts))
        tpl = tpl.replace('{{pnl}}', "{:,.0f}".format(_pnl))
    
        tpl = tpl.replace('{{gammaUpMatrix}}', _gammaUpMatrix.style.format('{:,.0f}').to_html())
        tpl = tpl.replace('{{gammaDownMatrix}}', _gammaDownMatrix.style.format('{:,.0f}').to_html())
    
        with open(FOLDER + 'reports/optionsToday.html', 'w', encoding='utf-8') as f:
            f.write(tpl)
        
        display_html(tpl, raw=True)
        
        
        
        
    def pnlReport(self) :
        
        _base_pricing_dt = self._pricing_dt
         
        total_mtm = '{:,.0f}'.format(self._assets['amount'].sum())    
        
        #YESTERDAY FIGURES
        d1_date = (_base_pricing_dt - CDay(1)).date()
        table = self.performanceAttribution2(d1_date, _base_pricing_dt)
        table.rename(columns = {'start_amt' : 'd1_start_amt',
                                'mvmts' : 'd1_mvmts',
                                'pnl' : 'd1_pnl',
                                'perf' : 'd1_perf',
                                'perfAttr' : 'd1_perfAttr'}, inplace=True)
        
        #MTD FIGURES
        mtd_date = (date(_base_pricing_dt.year, _base_pricing_dt.month, 1) - CDay(1)).date()
        mtd_table = self.performanceAttribution2(mtd_date, _base_pricing_dt)
        table[['mtd_start_amt', 'mtd_mvmts', 'mtd_pnl', 'mtd_perf', 'mtd_perfAttr']] = mtd_table[['start_amt', 'mvmts', 'pnl', 'perf', 'perfAttr']]
            
        _date = format(dt.now(), '%Y-%b-%d %H:%M')
                    
        d1_pnl = table['d1_pnl'].sum()
        d1_pnl_p = table['d1_perfAttr'].sum()
        mtd_pnl = table['mtd_pnl'].sum()
        mtd_pnl_p = table['mtd_perfAttr'].sum()
        
        self.basePort()
        
        tpl = ""
        with open(FOLDER + 'reports/pnlReport.html') as f:
            tpl = f.read()
            f.close()
        
        tpl = tpl.replace('{{date}}', _date)
        
        tpl = tpl.replace('{{pricing_dt}}', dt.strftime(_base_pricing_dt, '%d-%b-%y'))
        tpl = tpl.replace('{{total_mtm}}', total_mtm)
        
        tpl = tpl.replace('{{d1_pnl}}', "{:,.0f}".format(d1_pnl))
        tpl = tpl.replace('{{d1_pnl%}}', "{:,.2%}".format(d1_pnl_p))
        tpl = tpl.replace('{{mtd_pnl}}', "{:,.0f}".format(mtd_pnl))
        tpl = tpl.replace('{{mtd_pnl%}}', "{:,.2%}".format(mtd_pnl_p))
        
        tpl = tpl.replace('{{assets}}', table.style.format({'amount' : '{:,.0f}',
                                                            'd1_start_amt' : '{:,.0f}',
                                                            'd1_mvmts' : '{:,.0f}',
                                                            'd1_pnl' : '{:,.0f}',
                                                            'mtd_start_amt' : '{:,.0f}',
                                                            'mtd_mvmts' : '{:,.0f}',
                                                            'mtd_pnl' : '{:,.0f}',
                                                            '%' : '{:,.0%}',
                                                            'd1_perf' : '{:,.1%}',
                                                            'd1_perfAttr' : '{:,.2%}',
                                                            'mtd_perf' : '{:,.1%}',
                                                            'mtd_perfAttr' : '{:,.2%}'}).to_html())
    
        with open(FOLDER + 'reports/pnlToday.html', 'w', encoding='utf-8') as f:
            f.write(tpl)
        
        display_html(tpl, raw=True)
        
    
    def exposureReport() :
        pass
    
    def curveChange(self) :
        rates = self._securities._curves._zero.copy()
        _base_dt = self._securities._curves._pricing_dt
        
        d1_date = (self._pricing_dt - CDay(1)).date()
        self._securities._curves.pricing_dt = d1_date
        rates['d1_rate'] = self._securities._curves._zero['rate'].values
        rates['d1_diff'] = rates['rate'] - rates['d1_rate']
        
        mtd_date = (date(self._pricing_dt.year, self._pricing_dt.month, 1) - CDay(1)).date()
        self._securities._curves.pricing_dt = mtd_date
        rates['mtd_rate'] = self._securities._curves._zero['rate'].values
        rates['mtd_diff'] = rates['rate'] - rates['mtd_rate']
        
        self._securities._curves.pricing_dt = _base_dt
        
        print(rates)
        
    def all_assets(self) :
        
        _assets = self._port.pivot_table(values='mtm',
                                        index='asset_class', columns='currency',
                                        aggfunc='sum')
        _cash = self._cash[['mtm']].rename(columns={'mtm' : 'cash'}).T
        _table = pd.concat([_assets, _cash])
        
        #Add Sum and Order based on Sum
        _table.loc['sum'] = _table.sum(axis=0)
        _table = _table.iloc[:, (-_table.iloc[-1, :]).argsort()]
        #Remove Sum
        _table = _table.iloc[:-1]
        
        #Add Column Total and %
        _table['total'] = _table.sum(axis=1)
        _table['%'] = _table['total'] / _table['total'].sum()
        _table = _table.sort_values(by='total', ascending=False)
        
        #Re-add Row Total and %
        _table.loc['sum'] = _table.sum(axis=0)
        _table.loc['%'] = _table.loc['sum'] / _table.loc['sum'].sum() * 2
        
        #Return a style (to be improved)
        return _table.fillna('-').style.format(precision=2)






