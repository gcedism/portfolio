#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scipy.stats
from numpy import sqrt, log, exp, pi
from datetime import date

GAMMA = 0.05
VEGA_m = 5
VEGA_e = VEGA_m * 0.01
IMP_VOL_e = 0.01 # diff in price
IMP_VOL_max_it = 20

class Option :
    
    def __init__(self, c_p:str, S:float, K:float, r:float, i:float, t:float, vol:float) :
        """
        Base class for all options
        :parameters:
            c_p: str, 
                Call or Put 
            S : float,
                Spot price
            K : float,
                Strike price
            r: float,
                Base currency rate
            i : 
                Asset Interest Rate
            t : float
                Tenor
            vol : float,
                Volatility annualised
        """
        
        self._c_p = c_p
        self._S = S
        self._K = K
        self._r = r
        self._i = i
        self._t = t
        self._vol = vol
        self.calc_price()
        self.calc_delta()
        self.calc_gamma_up()
        self.calc_gamma_down()
        self.calc_vega_up()
        self.calc_vega_down()
        self.calc_mod_theta()
    
    def __call__(self) :
        self.desc()
    
    def desc(self) :
        spot = '{:.2f}'.format(self._S)
        strike = '{:.2f}'.format(self._K)
        r = '{:.2%}'.format(self._r)
        i = '{:.2%}'.format(self._i)
        t = '{:.1f}'.format(self._t)
        vol = '{:.2%}'.format(self.vol)
        price = '{:.2f}'.format(self.price)
        delta = '{:.1%}'.format(self.delta)
        gamma_up = '{:.2f}'.format(self.gamma_up)
        gamma_down = '{:.2f}'.format(self.gamma_down)
        vega_up = '{:.2f}'.format(self.vega_up)
        vega_down = '{:.2f}'.format(self.vega_down)
        theta = '{:.2f}'.format(self.theta)
        
        print('Option description')
        print('Asset : <asset>')
        print(f'Call or put : {self._c_p}')
        print(f'Current Spot Price : {spot}')
        print(f'Strike : {strike}')
        print(f'Base Currency Interest Rate : {r}')
        print(f'Asset Interest Rate (not used yet): {i}')
        print(f'Time to maturity (years) : {t}')
        print(f'Implied Volatility : {vol}')
        print(f'Current Price : {price}')
        print(f'Delta : {delta}')
        print(f'Gamma Up : {gamma_up}')
        print(f'Gamma Down : {gamma_down}')
        print(f'Vega Up : {vega_up}')
        print(f'Vega Down : {vega_down}')
        print(f'Theta : {theta}')
    
    def calc_price(self):
        N = scipy.stats.norm.cdf
        d1 = (log(self._S/self._K) + (self._r+self._vol**2/2)*self._t) / (self._vol*sqrt(self._t))
        d2 = d1 - self._vol * sqrt(self._t)
        if self._c_p == 'call':
            price = N(d1) * self._S - N(d2) * self._K * exp(-self._r*self._t)
        elif self._c_p == 'put':
            price = N(-d2) * self._K * exp(-self._r*self._t) - N(-d1) * self._S
        
        self._price = price
    
    @property
    def price(self) :
        return self._price
    @price.setter
    def price(self, new_price) :
        self._price = new_price
        self.calc_imp_vol()
        self.calc_delta()
        self.calc_gamma_up()
        self.calc_gamma_down()
        self.calc_vega_up()
        self.calc_vega_down()
        self.calc_mod_theta()
    
    @property
    def spot(self):
        return self._S
    @spot.setter
    def spot(self, _spot):
        self._S = _spot
        # Not yet implemented, because when spot changes, the vol needs to be interpolated
        # self.calc_price()
        # self.calc_delta()
        # self.calc_gamma_up()
        # self.calc_gamma_down()
        # self.calc_vega_up()
        # self.calc_vega_down()
        # self.calc_mod_theta()
    
    def calc_delta(self) :
        N = scipy.stats.norm.cdf
        d1 = (log(self._S/self._K) + (self._r+self._vol**2/2)*self._t) / (self._vol*sqrt(self._t))
    
        if self._c_p == 'call':
            self._delta =  N(d1)
        elif self._c_p == 'put':
            self._delta = N(d1) - 1
            
    @property
    def delta(self) :
        return self._delta
    
    def calc_gamma_up(self) :
        delta1 = self._delta
        self._S = self._S * (1+GAMMA)
        self.calc_delta()
        delta2 = self._delta
        self._gamma_up = delta2 - delta1
        
        #Return to normal levels
        self._S = self._S / (1+GAMMA)
        self.calc_delta()
        
    @property
    def gamma_up(self) :
        return self._gamma_up
    
    def calc_gamma_down(self) :
        delta1 = self._delta
        self._S = self._S * (1-GAMMA)
        self.calc_delta()
        delta2 = self._delta
        self._gamma_down = delta1 - delta2
        
        #Return to normal levels
        self._S = self._S / (1-GAMMA)
        self.calc_delta()
        
    @property
    def gamma_down(self) :
        return self._gamma_down

    def calc_vega_up(self) :
        price1 = self.price
        self._vol += VEGA_e
        self.calc_price()
        price2 = self.price
        
        self._vega_up = (price2-price1) / VEGA_m
        
        #Return to normal levels
        self._vol -= VEGA_e
        self.calc_price()
    
    @property
    def vega_up(self) :
        return self._vega_up
    
    def calc_vega_down(self) :
        price1 = self.price
        self._vol -= VEGA_e
        self.calc_price()
        price2 = self.price
        
        self._vega_down = (price2-price1) / VEGA_m
        
        #Return to normal levels
        self._vol += VEGA_e
        self.calc_price()

    @property
    def vega_down(self) :
        return self._vega_down
            
    @property
    def vega(self) :
        return (self._vega_up - self._vega_down) / 2
    
    def calc_mod_theta(self) :
        d = 1
        price1 = self._price
        self._t = (self._t * 365 - d) / 365
        self.calc_price()
        price2 = self.price
        
        self._theta = price2 - price1
        #Return to normal levels
        self._t = (self._t * 365 + d) / 365
        self.calc_price()
        
    @property
    def theta(self) :
        return self._theta
            
    def calc_imp_vol(self) :
        
        ## *** USING NEWTON RAPHSON METHOD ***************************
        # f(x) = price(vol)
        # f'(x) = vega(vol)
        # x1 = xo - fx / f'x
        ## ***********************************************************

        
        fx = IMP_VOL_e * 2 # initial standard error
        i = 0
        y = self._vol
        target_price = self._price
        
        while (abs(fx) >= IMP_VOL_e) and (i <= IMP_VOL_max_it):
            self.calc_price()
            fx = self._price - target_price
            self.calc_vega_up()
            self.calc_vega_down()
            dfx = self.vega * 100
              
            self._vol = self._vol - fx / dfx
            i += 1
        
    @property
    def vol(self) :
        return self._vol
    @vol.setter
    def vol(self, new_vol) :
        self._vol = new_vol
        self.calc_price()
        self.calc_delta()
        self.calc_gamma_up()
        self.calc_gamma_down()
        self.calc_vega_up()
        self.calc_vega_down()
        self.calc_mod_theta()
        
    
class SPYOption(Option) :
    
    def __init__(self, code:str, pricing_dt:date, price:float=None,
                 spot:float=392, r:float=0.03, i:float=0.01, vol:float=0.25) :
        # example code : SPY230317C00400000
        self._code = code
        if code[9] == 'C' :
            self._c_p = 'call'
        else : 
            self._c_p = 'put'
        self._K = float(code[-6:] ) / 1000
        maturity = date(int('20'+code[3:5]), int(code[5:7]), int(code[7:9]))
        self._t = (maturity - pricing_dt).days/365
        self._vol = vol 
        self._r = r
        self._i = i
        self._S = spot
        self.price = price

        
    @property
    def code(self) :
        return self._code
    