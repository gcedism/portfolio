from datetime import date

from .bond import Bond

class Future :
    
    def __init__(self, code:str) :
        self._code = code
        self._maturity = date(2023, 3, 31)
        self._asset = 'us_treasury'
        self._price = 109.00

class USTFuture(Future) :
    
    def __init__(self, code:str) :
        Future.__init__(self, code)
        self.CTD()
        self._ctd.cf = self.CF(self._ctd)
        self.dv01()
        
    def CTD(self) :
        _mat = date(2027, 5, 31)
        _cpn = 2.625
        _price = 95.0078095
        pricing_dt = date(2023, 3, 31)
        self._ctd = Bond(_mat, _cpn, _price, pricing_dt)
        
    def CF(self, bond:Bond) -> float:
        _tempY = bond.y
        bond.y = 0.06
        cf = bond.cl_price / 100
        bond.y = _tempY
        return cf
        
    def dv01(self) :
        _price = self._price * self._ctd.cf
        _tempP = self._ctd.cl_price
        self._ctd.cl_price = _price
        self._dv01 = self._ctd.dv01
        self._ctd.cl_price = _tempP