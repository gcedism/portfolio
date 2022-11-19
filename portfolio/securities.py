import pandas as pd
from datetime import datetime as dt
from _data.get_prices import hist
from .bond import bond


class securities:
  bonds = pd.read_csv('_data/bonds.csv', encoding='UTF-8', index_col=0)
  bonds.loc[:, 'maturity'] = bonds.loc[:, 'maturity'].map(
    lambda x: dt.strptime(x, '%Y-%m-%d').date())

  equities = pd.read_csv('_data/equities.csv', encoding='UTF-8', index_col=0)
  funds = pd.read_csv('_data/funds.csv', encoding='UTF-8', index_col=0)

  @classmethod
  def update(cls, pricing_dt):
    cls.bonds['price'] = cls.bonds.apply(lambda x: hist.loc[pricing_dt, x.name]
                                         if x.name in hist.columns else 100,
                                         axis=1)
    cls.bonds['Bond'] = cls.bonds.apply(
      lambda x: bond(x['maturity'], x['cpn'], x['price'], pricing_dt), axis=1)
    cls.bonds[['yield', 'spread', 'dur']] = cls.bonds.apply(
      lambda x: pd.Series(
        [x['Bond'].y * 100, x['Bond'].spread * 10000, x['Bond'].duration],
        index=['yield', 'spread', 'duration']),
      axis=1)

    cls.equities['price'] = cls.equities.apply(
      lambda x: hist.loc[pricing_dt, x.name] if x.name in hist.columns else 0,
      axis=1)

    cls.funds['price'] = cls.funds.apply(lambda x: hist.loc[pricing_dt, x.name]
                                         if x.name in hist.columns else 0,
                                         axis=1)

    cls.fx = pd.DataFrame({'id': ['USD', 'EUR', 'CHF', 'CAD', 'BRL']},
                          index=['USD', 'EUR=X', 'CHF=X', 'CAD=X', 'BRL=X'])
    cls.fx['price'] = cls.fx.apply(lambda x: hist.loc[pricing_dt, x.name]
                                   if x.name in hist.columns else 1,
                                   axis=1)
    cls.fx.set_index('id', inplace=True)
