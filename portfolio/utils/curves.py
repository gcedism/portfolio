#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import pandas as pd
import numpy as np
import requests
import warnings
from datetime import datetime as dt
from datetime import timedelta as td
from datetime import date

class Curves :
    
    def __init__(self, country:str, initial_pricing_dt:date) :
        """
        Generates Curves
        :Parameters:
            country : Str, 
                Country
            pricing_dt : date,
                Initial Pricing Date
        """
        
        self._country = country
        self._pricing_dt = initial_pricing_dt
        self._depositsHistory = {}
        self._govtHistory = {}
        
        self.downloadDeposits()
        self.updateDeposits()
        
        self.downloadGovt()
        self.updateGovt()
        
        self.updateZero()
        
    def downloadDeposits(self) :
        
        if self._country == 'us' :
            if 'us' not in self._depositsHistory.keys() :
                params = {
                    'startDt' : '2020-12-01',
                    'endDt' : dt.strftime(self._pricing_dt, '%Y-%m-%d'),
                    'eventCodes' : '525',
                    'productCode' : '50',
                    'sort' : 'postDt:-1,eventCode:1',
                    'format' : 'xlsx'
                }
                p_excel = {
                    'index_col': 0,
                    'engine': 'openpyxl',
                    'usecols' : [0, 13, 14, 15, 16] 
                }
                url = 'https://markets.newyorkfed.org/read?'
        
                r = requests.get(url, params=params)
                with warnings.catch_warnings(record=True):
                    warnings.simplefilter("always")
                    df = pd.read_excel(r.content, **p_excel)
            
                df.index = df.index.map(lambda x : dt.strptime(x, '%m/%d/%Y').date())
                df.columns = [30, 90, 180, 'index']
                
                #Adjustment for FallBack spreads
                fb_spreads = {
                    30 : 0.11448,
                    90 : 0.26161,
                    180 :0.42826
                }
                for col in fb_spreads :
                    df.loc[:, col] += fb_spreads[col]
                    
                self._depositsHistory['us'] = df.sort_index()
    
    def updateDeposits(self) :
        idx = self._depositsHistory[self._country].index.get_indexer([self._pricing_dt], method='nearest')
        self._deposits = self._depositsHistory[self._country].iloc[idx].loc[:, [30, 90, 180]].T
     
    def downloadGovt(self) :
        
        if self._country == 'us' :
            if 'us' not in self._govtHistory.keys() :
                params = {
                    'type' : 'daily_treasury_yield_curve',
                    'field_tdr_date_value' : '2022',
                    '_format' : 'csv'
                }
                p_csv = {
                    'index_col': 0,
                }
                url = ' https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/' + str(self._pricing_dt.year) + '/all?'
        
                r = requests.get(url, params=params).content
                df = pd.read_csv(io.StringIO(r.decode('utf-8')), **p_csv)
            
                df.index = df.index.map(lambda x : dt.strptime(x, '%m/%d/%Y').date())
                df.columns = [30, 60, 90, 120, 180,
                              365, 730, 1095, 1825, 
                              2555, 3650, 7300, 10950]
                self._govtHistory['us'] = df.sort_index()
                
    def updateGovt(self) :
        idx = self._govtHistory[self._country].index.get_indexer([self._pricing_dt], method='nearest')
        self._govt = self._govtHistory[self._country].iloc[idx].T
         
    def updateZero(self) :
        
        _zero = self._deposits.copy()
        _zero.columns = ['rate']
        _zero['df'] = 1 / ( 1 + _zero['rate'] * _zero.index / 36000 )
        
        next_ust = self._govt.loc[self._govt.index > _zero.index[-1]]
        max_j = 20
        j = 0
        while (not next_ust.empty) & (j <= max_j) :
            
            _maturity = self._pricing_dt + td(days=int(next_ust.index[0]))
            _coupon = next_ust.iloc[0, 0]
            ust = self.cash_flow(_maturity, _coupon, pricing_dt=self._pricing_dt)
            ust['zero_df'] = (ust.join(_zero, how='outer')
                             .astype(float)
                             .sort_index()
                             .interpolate('index')
                             .loc[ust.index, 'df'])                 
            
            y = _coupon
            ust['origin_pv'] = ust.apply(lambda x : x['flow'] / ( (1 + y / 200) ** (x.name/180) ), axis = 1)
            ust['bootstrap_pv'] = ust['flow'] * ust['zero_df']                
                
            e = 0.001
            max_it = 20
            diff = 0.02
            i = 0
            zero_y = _coupon

            while (diff > e) & (i <= max_it) :
                if (ust['origin_pv'].sum() - ust['bootstrap_pv'].sum()) > 0 :
                    zero_y -= 0.01
                else : 
                    zero_y -= 0.01
                
                ust.loc[ust.index>_zero.index[-1], 'zero_df'] = ust.loc[ust.index>_zero.index[-1]].index.map(lambda x:  1 / ( 1 + zero_y * x / 36500 ))
                ust.loc[:, 'bootstrap_pv'] = ust['flow'] * ust['zero_df']
                diff = abs(ust['origin_pv'].sum() - ust['bootstrap_pv'].sum())
                i += 1 
            
            _zero.loc[ust.index[-1], 'rate'] = zero_y
            _zero.loc[ust.index[-1], 'df'] = 1 / ( 1 + zero_y * ust.index[-1] / 36500 )
                
            next_ust = self._govt.loc[self._govt.index > _zero.index[-1]]
            j += 1
        
        
        #Adjustment on the index (maybe not necessary in the future)
        _zero['dates'] = _zero.index.map(lambda x : self._pricing_dt + td(days=int(x)))
        _zero.set_index('dates', inplace=True)
        self._zero = _zero
    
    @property
    def deposits(self) :
        return self._deposits
    
    @property
    def govt(self) :
        return self._govt
    
    @property
    def zero(self) :
        return self._zero
    
    @property
    def pricing_dt(self) :
        return self._pricing_dt
    @pricing_dt.setter
    def pricing_dt(self, new_dt:date) :
        self._pricing_dt = new_dt
        self.updateDeposits()
        self.updateGovt()
        self.updateZero()
    
    @staticmethod
    def cash_flow(maturity:date, coupon:float, pricing_dt:date=dt.now().date(),
                   freq:int=6) -> pd.DataFrame:
        _cshf = {
            'dates': [maturity],
            'flow': [100 + coupon / (12 / freq)]
        }
        new_year = maturity.year + ((maturity.month - freq) < 0) * - 1
        new_month = (maturity.month - freq) % 12
        if new_month == 0 :
            new_month = 12
        try :
            _date = date(new_year, new_month, maturity.day) # if 31 works
        except :
            try :
                _date = date(new_year, new_month, maturity.day-1) # 30 works
            except :
                try :
                    _date = date(new_year, new_month, maturity.day-2) # 29 works
                except :
                    _date = date(new_year, new_month, maturity.day-3) # 28 works

        while _date > pricing_dt:
            _cshf['dates'].append(_date)
            _cshf['flow'].append(coupon / (12 / freq))
            new_year = _date.year + ((_date.month - freq) <= 0) * - 1
            new_month = (_date.month - freq) % 12
            if new_month == 0 :
                new_month = 12
            try :
                _date = date(new_year, new_month, maturity.day) # if 31 works
            except :
                try :
                    _date = date(new_year, new_month, maturity.day-1) # 30 works
                except :
                    try :
                        _date = date(new_year, new_month, maturity.day-2) # 29 works
                    except :
                        _date = date(new_year, new_month, maturity.day-3) # 28 works

        cshf = pd.DataFrame(_cshf).set_index('dates').sort_index()
        cshf['days'] = (cshf.index - pricing_dt).days
        cshf = cshf.set_index('days').sort_index()
        
        return cshf
        