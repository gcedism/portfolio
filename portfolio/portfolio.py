#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import Reports, Performance

class Portfolio(Reports, Performance) :
    
    @property
    def name(self):
        return self._name
    
    @property
    def port(self):
        return self._port
    
    @property
    def currencies(self):
        return self._currencies
    
    @property
    def assets(self):
        return self._assets
    
    @property
    def bonds(self):
        return self._bonds
                
    @property
    def equities(self):
        return self._equities
    
    @property
    def options(self) :
        return self._options
        
    @property
    def cash(self):
        display_cash = self._cash.style.format({
                    "amount": "{:,.2f}",
                    "ccy_price": "{:,.4f}",
                    "mtm": "{:,.2f}"
                    })
        return display_cash
        