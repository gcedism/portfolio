#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from IPython.display import display_html
from datetime import datetime as dt

from .base import BasePortfolio

FOLDER = __file__[:-len('base/reports.py')]

class Reports(BasePortfolio) :
    
    def OptionsReport(self) :
        tpl = ""
        with open(FOLDER + 'reports/options.html') as f:
            tpl = f.read()
            f.close()
        date = format(dt.now(), '%Y-%b-%d %H:%M')
        tpl = tpl.replace('{{date}}', date)
        tpl = tpl.replace('{{mainTitle}}', 'Options Report')
        tpl = tpl.replace('{{optionsDelta}}', "{:,.0f}".format(self._options._totalDelta))
        tpl = tpl.replace('{{portDelta}}', "{:,.0f}".format(self._assets.loc['option', 'amount']))
        tpl = tpl.replace('{{totalDelta$}}', "{:,.0f}".format(self._assets.loc['option', 'amount'] + self._options._totalDelta))
        tpl = tpl.replace('{{totalDelta%}}', "{:.2%}".format((self._assets.loc['option', 'amount'] + self._options._totalDelta) / self._assets['amount'].sum() / 100))
        tpl = tpl.replace('{{gamma}}', "{:,.0f}".format(self._options._totalGamma))
        tpl = tpl.replace('{{theta}}', "{:,.0f}".format(self._options._totalTheta))
        tpl = tpl.replace('{{mtm}}', "{:,.0f}".format(self._options._mtm))
    
        _gammaUpMatrix = self._options.gammaUpMatrix.copy()
        _gammaUpMatrix.columns = np.round(_gammaUpMatrix.columns, 2).astype(str)
        _gammaDownMatrix = self._options.gammaDownMatrix.copy()
        _gammaDownMatrix.columns = np.round(_gammaDownMatrix.columns, 2).astype(str)
    
        tpl = tpl.replace('{{gammaUpMatrix}}', _gammaUpMatrix.style.format('{:,.0f}').to_html())
        tpl = tpl.replace('{{gammaDownMatrix}}', _gammaDownMatrix.style.format('{:,.0f}').to_html())
    
        with open(FOLDER + 'reports/optionsToday.html', 'w', encoding='utf-8') as f:
            f.write(tpl)
        
        display_html(tpl, raw=True)
    
    
    






