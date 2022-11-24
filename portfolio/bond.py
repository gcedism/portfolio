import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td


class Bond():

  us_zero = pd.read_csv('_data/us_zero.csv', index_col=0)
  us_zero.index = us_zero.index.map(
    lambda x: dt.strptime(x, '%Y-%m-%d').date())

  def __init__(self,
               maturity: dt.date,
               coupon: float,
               cl_price: float,
               pricing_dt=dt.now().date(),
               freq=6):
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

  def _cash_flow(self):
    _cshf = {
      'dates': [self.maturity],
      'flow': [100 + self.coupon / (12 / self.freq)]
    }
    _date = (self.maturity - td(days=int(365 / (12 / self.freq))))

    while _date > self.pricing_dt:
      _cshf['dates'].append(_date)
      _cshf['flow'].append(self.coupon / (12 / self.freq))
      _date = (_date - td(days=int(365 / (12 / self.freq))))

    self.cshf = (pd.DataFrame(_cshf).set_index('dates').sort_index())
    self.cshf['days'] = (self.cshf.index - self.pricing_dt).days

  def _calcAcc(self):
    last_acc = (self.cshf.index[0] - td(days=int(365 / (12 / self.freq))))
    self._acc = self.coupon / (12 / self.freq) * (
      self.pricing_dt - last_acc).days / (int(365 / (12 / self.freq)))

  def _calc_yield(self):

    ## *** USING NEWTON RAPHSON METHOD ***************************
    # f(x) = sum ( flow / (1 + yield / 2) ^ (days/180) )
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
      fx = self.cshf.apply(lambda x: x['flow'] /
                           ((1 + y / 2)**(x['days'] / 180)),
                           axis=1).sum() - self._pv
      dfx = self.cshf.apply(lambda x: -x['flow'] * x['days'] / (2 * 180) *
                            ((y / 2 + 1)**(-x['days'] / 180 - 1)),
                            axis=1).sum()
      y = y - fx / dfx
      i += 1

    self.y = y

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

    _cshf = self.cshf.join(
      Bond.us_zero['df'],
      how='outer').sort_index().interpolate().loc[self.cshf.index]
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

    self.spread = spread

  def _calc_duration(self):

    aux = np.arange(1, self.cshf.shape[0] + 1)
    pv = self.cshf.apply(lambda x: x['flow'] /
                         ((1 + self.y / 2)**(x['days'] / 180)),
                         axis=1)
    md = aux * pv

    self.duration = md.sum() / self._pv / (12 / self._freq)

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
