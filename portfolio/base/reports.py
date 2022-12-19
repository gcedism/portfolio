#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
            self.totalUpdate(mtd_date) 
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
            
                        
        tpl = ""
        with open(FOLDER + 'reports/options.html') as f:
            tpl = f.read()
            f.close()
        _date = format(dt.now(), '%Y-%b-%d %H:%M')
        tpl = tpl.replace('{{date}}', _date)
        tpl = tpl.replace('{{mainTitle}}', 'Options Report')
        tpl = tpl.replace('{{optionsDelta}}', "{:,.0f}".format(self._options._totalDelta))
        
        _portDelta = 0
        if 'equity' in self._assets.index :
            _portDelta += self._assets.loc['equity', 'amount']
        if 'equities' in self._assets.index :
            _portDelta += self._assets.loc['equities', 'amount']
        if 'multi-asset' in self._assets.index :
            _portDelta += self._assets.loc['multi-asset', 'amount']
        tpl = tpl.replace('{{portDelta}}', "{:,.0f}".format(_portDelta))
        
        _totalDelta = _portDelta + self._options._totalDelta
        tpl = tpl.replace('{{totalDelta$}}', "{:,.0f}".format(_totalDelta))
        
        _totalMtm = self._assets['amount'].sum()
        
        _totalDeltaPer = _totalDelta / _totalMtm / 100
        tpl = tpl.replace('{{totalDelta%}}', "{:.2%}".format(_totalDeltaPer))
        
        tpl = tpl.replace('{{gamma}}', "{:,.0f}".format(self._options._totalGamma))
        tpl = tpl.replace('{{theta}}', "{:,.0f}".format(self._options._totalTheta))
                
        tpl = tpl.replace('{{mtm}}', "{:,.0f}".format(_totalMtm))
        tpl = tpl.replace('{{mtm_mtd}}', "{:,.0f}".format(_totalMtm_Mtd))
        
        tpl = tpl.replace('{{cashMvmts}}', "{:,.0f}".format(_cashMvmts))
        
        _pnl = _totalMtm - _cashMvmts - _totalMtm_Mtd 
        
        tpl = tpl.replace('{{pnl}}', "{:,.0f}".format(_pnl))
    
        _gammaUpMatrix = self._options.gammaUpMatrix.copy()
        _gammaUpMatrix.columns = np.round(_gammaUpMatrix.columns, 2).astype(str)
        _gammaDownMatrix = self._options.gammaDownMatrix.copy()
        _gammaDownMatrix.columns = np.round(_gammaDownMatrix.columns, 2).astype(str)
    
        tpl = tpl.replace('{{gammaUpMatrix}}', _gammaUpMatrix.style.format('{:,.0f}').to_html())
        tpl = tpl.replace('{{gammaDownMatrix}}', _gammaDownMatrix.style.format('{:,.0f}').to_html())
    
        with open(FOLDER + 'reports/optionsToday.html', 'w', encoding='utf-8') as f:
            f.write(tpl)
        
        display_html(tpl, raw=True)
    
    
    






