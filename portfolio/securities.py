import pandas as pd
from datetime import datetime as dt
from datetime import date
from .._data.p_get_prices import hist # using private import
# from .._data._get_prices import hist
from .bond import Bond
from .options import SPYOption

FOLDER = __file__[:-len('portfolio/securities.py')]

class Securities:
    """
    Main Class that gathers basic information about a list of possible securities
    """
    
    bonds = pd.read_csv(FOLDER + '_data/bonds.csv', encoding='UTF-8', index_col=0)
    bonds.loc[:, 'maturity'] = bonds.loc[:, 'maturity'].map(lambda x: dt.strptime(x, '%Y-%m-%d').date())

    equities = pd.read_csv(FOLDER + '_data/equities.csv', encoding='UTF-8', index_col=0)

    funds = pd.read_csv(FOLDER + '_data/funds.csv', encoding='UTF-8', index_col=0)
    
    options = pd.read_csv(FOLDER + '_data/options.csv', encoding='UTF-8', index_col=0)


    @classmethod
    def update(cls, pricing_dt:date):
        """
        Updates pricing from a previously downloaded data
        :parameters:
            pricing_dt: date
                Reference pricing date
        """
        
        
        cls.bonds['price'] = cls.bonds.apply(lambda x: hist.loc[pricing_dt, x.name]
                                         if x.name in hist.columns else 100,
                                         axis=1)
        cls.bonds['Bond'] = cls.bonds.apply(lambda x: Bond(x['maturity'], x['cpn'], x['price'], pricing_dt), axis=1)
        cls.bonds[['yield', 'spread', 'dur']] = cls.bonds.apply(lambda x: 
                                                                pd.Series([x['Bond'].y * 100,
                                                                           x['Bond'].spread * 10000,
                                                                           x['Bond'].duration],
                                                                          index=['yield', 'spread', 'duration']), axis=1)
    
        
        cls.equities['price'] = cls.equities.apply(lambda x: hist.loc[pricing_dt, x.name]
                                                   if x.name in hist.columns else 0, axis=1)
        
        
        cls.funds['price'] = cls.funds.apply(lambda x: hist.loc[pricing_dt, x.name]
                                             if x.name in hist.columns else 0, axis=1)
        
        
        cls.fx = pd.DataFrame({'id': ['USD', 'EUR', 'CHF', 'CAD', 'BRL', 'GBP']},
                              index=['USD', 'EUR=X', 'CHF=X', 'CAD=X', 'BRL=X', 'GBP=X'])
        
        
        cls.fx['price'] = cls.fx.apply(lambda x: hist.loc[pricing_dt, x.name]
                                       if x.name in hist.columns else 1, axis=1)
        cls.fx.set_index('id', inplace=True)
        
        cls.options['price'] = cls.options.apply(lambda x: hist.loc[pricing_dt, x.name]
                                         if x.name in hist.columns else 1,
                                         axis=1)
        cls.options['Option'] = cls.options.index.map(lambda x: SPYOption(x, pricing_dt))
        for i in range(cls.options.shape[0]) :
            cls.options.iloc[i]['Option'].price = cls.options.iloc[i]['price']
    
        
        
        
        
        
