import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
from datetime import date


class Bond():
    
    def __init__(self, maturity:date, coupon:float, cl_price:float, us_zero:pd.DataFrame, pricing_dt:date=dt.now().date(),
                 freq:int=6):
        """
        Class that calculates factor for a Bond
        :parameters:
            maturity : date,
                Maturity
                
            coupon : float,
                Coupon
                
            cl_price : float,
                Clean Price
                
            us_zero : pd.DataFrame,
                DataFrame with the Us Curve to be used to calculate the Spread
                
            pricing_dt : date,
                Pricing Date
                
            freq : int,
                Frequency
                
        :methods:
            yield
            
            spread
            
            duration
            
            price
            
        """
        self._us_zero = us_zero
        self._maturity = maturity
        self._coupon = coupon
        self._freq = freq
        self._cl_price = cl_price
        self._pricing_dt = pricing_dt
        self._cash_flow()
        self._calcAcc()
        self._pv = self._cl_price + self._acc
        self._calc_yield()
        self._calc_spread()
        self._calc_duration()
        self._calc_dv01()
        
    def _cash_flow(self):
        _cshf = {
            'dates': [self._maturity],
            'flow': [100 + self.coupon / (12 / self.freq)]
        }
        new_year = self._maturity.year + ((self._maturity.month - self._freq) < 0) * - 1
        new_month = (self._maturity.month - self._freq) % 12
        if new_month == 0 :
            new_month = 12
        try :
            _date = date(new_year, new_month, self._maturity.day) # if 31 works
        except :
            try :
                _date = date(new_year, new_month, self._maturity.day-1) # 30 works
            except :
                try :
                    _date = date(new_year, new_month, self._maturity.day-2) # 29 works
                except :
                    _date = date(new_year, new_month, self._maturity.day-3) # 28 works

        while _date > self._pricing_dt:
            _cshf['dates'].append(_date)
            _cshf['flow'].append(self._coupon / (12 / self._freq))
            new_year = _date.year + ((_date.month - self._freq) <= 0) * - 1
            new_month = (_date.month - self._freq) % 12
            if new_month == 0 :
                new_month = 12
            try :
                _date = date(new_year, new_month, self._maturity.day) # if 31 works
            except :
                try :
                    _date = date(new_year, new_month, self._maturity.day-1) # 30 works
                except :
                    try :
                        _date = date(new_year, new_month, self._maturity.day-2) # 29 works
                    except :
                        _date = date(new_year, new_month, self._maturity.day-3) # 28 works

        self._cshf = (pd.DataFrame(_cshf).set_index('dates').sort_index())
        self._cshf['days'] = (self._cshf.index - self._pricing_dt).days

    def _calcAcc(self):
        _date = self._cshf.index[0]
        new_year = _date.year + ((_date.month - self._freq) < 0) * - 1
        new_month = (_date.month - self._freq) % 12
        if new_month == 0 :
            new_month = 12
        try :
            last_acc = date(new_year, new_month, self._maturity.day) # if 31 works
        except :
            try :
                last_acc = date(new_year, new_month, self._maturity.day-1) # 30 works
            except :
                try :
                    last_acc = date(new_year, new_month, self._maturity.day-2) # 29 works
                except :
                    last_acc = date(new_year, new_month, self._maturity.day-3) # 28 works
        
        self._acc = self._coupon / (12 / self._freq) * (self._pricing_dt - last_acc).days / (365 / (12 / self._freq))

    def _calc_yield(self):

        ## *** USING NEWTON RAPHSON METHOD ***************************
        # f(x) = sum ( flow / (1 + yield / 2) ^ (days/182.5) )
        # f(x) = sum ( c / (b + a.x)^d )
        #        a = 1/2
        #        b = 1
        #        c = flow
        #        d = days/180
        # f'(x) = sum ( - a.c.d / (b + a.x)^(-d-1) )
        # x1 = xo - fx / f'x
        ## ***********************************************************

        e = 0.01
        fx = 0.02
        max_it = 10
        i = 0
        y = self._coupon / 100
        while (abs(fx) >= e) and (i <= max_it):
            fx = self._cshf.apply(lambda x: x['flow'] /
                           ((1 + y / 2)**(x['days'] / (365/(12/self._freq)))),
                           axis=1).sum() - self._pv
            dfx = self._cshf.apply(lambda x: -x['flow'] * x['days'] / (2 * (365/(12/self._freq))) *
                            ((y / 2 + 1)**(-x['days'] / (365/(12/self._freq)) - 1)),
                            axis=1).sum()
            y = y - fx / dfx
            i += 1

        self._y = y
        
    def _calc_spread(self):

        ## *** USING NEWTON RAPHSON METHOD ***************************
        # f(x) = sum ( flow / (1 + (z_yield + spread) * days / 360 ) )
        # f(x) = sum( c / (b + a.x) )
        #        a = days / 360
        #        b = 1 + z_yield * days/360
        #        c = flow
        # f'(x) = sum ( - a.c / (b + a.x)^2 )
        # x1 = xo - fx / f'x
        ## ***********************************************************

        _cshf = self._cshf.join(self._us_zero['df'], how='outer').sort_index()
        _cshf.index = pd.DatetimeIndex(_cshf.index)
        _cshf = _cshf.astype(float).interpolate(method='time', limit_direction='both').loc[self._cshf.index]
        _cshf['zero_y'] = _cshf.apply(lambda x:
                                  (1 / x['df'] - 1) * 360 / x['days'],
                                  axis=1)
        spread = 0.01
        e = 0.001
        max_it = 10
        i = 0
        fx = 0.02
        dfx = 1

        while (abs(fx) > e and i <= max_it):
            fx = _cshf.apply(lambda x: x['flow'] /
                       (1 + (x['zero_y'] + spread) * x['days'] / 360),
                       axis=1).sum() - self._pv
            dfx = _cshf.apply(lambda x: -(x['flow'] * x['days'] / 360) / (
        (spread * x['days'] / 360 + 1 + x['zero_y'] * x['days'] / 360)**2),
                        axis=1).sum()

            spread = spread - fx / dfx
            i += 1

        self._spread = spread

    def _calc_duration(self):

        pv = self._cshf.apply(lambda x: x['flow'] /
                         ((1 + self._y / 2)**(x['days'] / (365/(12/self._freq)))),
                         axis=1)
        md = self._cshf.loc[:, 'days'] * pv

        self._duration = md.sum() / self._pv / 365
    
    def _calc_dv01(self) :
        
        pv_01 = self._cshf.apply(lambda x : x['flow'] / ((1 + (self._y+0.0001) / 2 ) ** (x['days'] / (365/(12/self._freq)))), axis=1).sum()
        pv_001 = self._cshf.apply(lambda x : x['flow'] / ((1 + (self._y-0.0001) / 2 ) ** (x['days'] / (365/(12/self._freq)))), axis=1).sum()
        self._dv01 = (pv_001 - pv_01)/2 * 1_000
    
    @property
    def cshf(self) :
        return self._cshf
    
    @property
    def maturity(self):
        return self._maturity

    @property
    def coupon(self):
        return self._coupon

    @property
    def freq(self):
        return self._freq

    @property
    def cl_price(self):
        return self._cl_price
    @cl_price.setter
    def cl_price(self, new_price: float):
        if new_price < 0:
            print('Please input a positive number')
        else:
            self._cl_price = new_price
            self._pv = new_price + self._acc
            self._calc_yield()
            self._calc_spread()
            self._calc_duration()
            self._calc_dv01()
    
    @property
    def y(self) :
        return self._y
    @y.setter
    def y(self, new_y:float) :
        self._y = new_y
        self.cshf['pv'] = self.cshf.apply(lambda x : x['flow'] / ((1 + new_y / 2 ) ** (x['days'] / (365/(12/self._freq)))), axis=1)
        self._pv = self.cshf['pv'].sum()
        self._cl_price = self._pv - self._acc
        self._calc_spread()
        self._calc_duration()
        self._calc_dv01()
        
    @property
    def spread(self) :
        return self._spread
    
    @property
    def pricing_dt(self):
        return self._pricing_dt
    @pricing_dt.setter
    def pricing_dt(self, date: dt.date):
        self._pricing_dt = date
        self._cash_flow()
        self._calcAcc()
        self._pv = self.cl_price + self._acc
        self._calc_yield()
        self._calc_spread()
        self._calc_duration()

    @property
    def dv01(self):
        return self._dv01
    
    @property
    def duration(self):
        return self._duration
    
    @property
    def us_zero(self) :
        return self._us_zero
    @us_zero.setter
    def us_zero(self, new_zero) :
        self._us_zero = new_zero
        self._calc_spread()
    
    'Method used for us_zero curve bootsrapp (maybe it should not be here)'
    @staticmethod
    def cash_flow(maturity, cpn, pricing_date=dt.now().date(), freq=6):
        #Standard Cash flow with bullet amortizatioon

        cshf = {'dates': [maturity], 'flow': [100 + cpn / (12 / freq)]}
        date = (maturity - td(days=int(365 / (12 / freq))))

        while date > pricing_date:
            cshf['dates'].append(date)
            cshf['flow'].append(cpn / (12 / freq))
            date = (date - td(days=int(365 / (12 / freq))))

        result = (pd.DataFrame(cshf).set_index('dates').sort_index())

        return result