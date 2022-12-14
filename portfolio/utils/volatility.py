import sys 
import os
import yfinance as yf
import pandas as pd
import numpy as np
from itertools import product as prod
from datetime import date

# sys.path.append(os.getcwd() + '/..')
from ..options import SPYOption

def vol_curve(pricing_dt:date, r:float, i:float) -> pd.DataFrame :
    
    spot = yf.Ticker('SPY').history()['Close'][-1]
    
    maturities = ['230120', '230317', '230616', '231215']
    c_strikes = np.array([1, 1.075, 1.1375, 1.25]) * spot
    c_strikes = (c_strikes / 5).round().astype(int) * 5
    p_strikes = np.array([0.75, 0.8625, 0.925]) * spot
    p_strikes = (p_strikes / 5).round().astype(int) * 5

    codes = [
        'SPY' + m + 'C' + '00' + str(s) + '000' 
        for m, s in prod(maturities, c_strikes)
        ]+[
        'SPY' + m + 'P' + '00' + str(s) + '000' 
        for m, s in prod(maturities, p_strikes)
    ]
    
    last_price = yf.download(codes, period='1mo')['Adj Close']
    
    
    last_prices = {x:last_price[x].dropna()[-1] for x in last_price}
    spy_opt = []
    
    for code in last_prices :
        opt = SPYOption(code, pricing_dt)
        opt.spot = spot
        opt.price = last_prices[code]
        spy_opt.append(opt)
    
    table = pd.DataFrame([{'strike': x._K, 'tenor' : x._t, 'vol' : x.vol} for x in spy_opt])

    table = table.pivot_table(values='vol', index='tenor', columns='strike', aggfunc='sum')

    return table