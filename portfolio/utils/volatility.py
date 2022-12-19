import sys 
import os
import yfinance as yf
import pandas as pd
import numpy as np
from itertools import product as prod
from datetime import date

import matplotlib.pyplot as plt
from matplotlib import cm

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
        opt = SPYOption(code, pricing_dt, price=last_prices[code], spot=spot)
        spy_opt.append(opt)
    
    table = pd.DataFrame([{'strike': x._K, 'tenor' : round(x._t, 2), 'vol' : x.vol} for x in spy_opt])

    table = table.pivot_table(values='vol', index='tenor', columns='strike', aggfunc='sum')

    return table

def printCurve2(*tables) :
    
    plt.style.use('_mpl-gallery')
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(12,10))
    
    for i, table in enumerate(tables) : 
        # Make data
        X = table.columns
        Y = table.index
        X, Y = np.meshgrid(X, Y)
        Z = table.values

        # Plot the surface
        if i == len(tables)-1 :
            ls = 'solid'
            color = 'blue'
        else :
            ls = 'dotted'
            color = 'red'
        ax.plot_wireframe(X, Y, Z, color=color, ls=ls)
    
    ax.view_init(elev=40, azim=55)
    ax.set_xlabel('Strike', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tenor', fontsize=12, fontweight='bold')
    ax.set_zlabel('Volatility', fontsize=12, fontweight='bold')
    plt.show()