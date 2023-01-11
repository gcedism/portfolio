# <span style="color:darkblue">Financial Portfolio</span>
---

## IMPLEMENTED : Newton-Rhapson for BOND SPREAD calculation

---
### Initial Set Up : 

- Portfolio needs to receive the following information :
    + Pricing Date : Initial Pricing date of the portfolio
    + Hist : Object with historical prices (used from the Portfolio.utils)
    + US Zero Curve : Curve to be used to calculate Bond Spreads (from Portfolio.utils)
    + Volatilities : Object with volatilities for options (used from the Portfolio.utils)
    + Asset Class products : list of products to be used in the Securities object
    + Securities : description of all securities with all calculattions (used from the Portfolio.securities)

![Initial](https://github.com/gcedism/portfolio/blob/main/docs/initial_setup.png "Initial")

- Portfolio Implementation : 
![portfolio](https://github.com/gcedism/portfolio/blob/main/docs/portfolio.png "portfolio")

### Features

- Breakdown of assets in Asset Classes / Currencies
![AllAssets](https://github.com/gcedism/portfolio/blob/main/docs/all_assets.png "Assets")

- Daily pnl Report
![Pnl](https://github.com/gcedism/portfolio/blob/main/docs/pnlReport.png "Pnl")

- Expected Cash Flow
![CashFlow](https://github.com/gcedism/portfolio/blob/main/docs/Cashflow1.png "Cashflow")
![CashFlow](https://github.com/gcedism/portfolio/blob/main/docs/Cashflow2.png "Cashflow")

- Historical Performance
![Performance](https://github.com/gcedism/portfolio/blob/main/docs/performance.png "Performance")

- Performance Attribution for different Asset Classes
![Performance Attribution](https://github.com/gcedism/portfolio/blob/main/docs/perf%20attribution.png "Performance Attribution")

- Portfolio Cash Breakdown :
![Cash](https://github.com/gcedism/portfolio/blob/main/docs/cash.png "cash")

- Portfolio Currencies Breakdown
![currencies](https://github.com/gcedism/portfolio/blob/main/docs/currencies.png "currencies")

- Equities
![equities](https://github.com/gcedism/portfolio/blob/main/docs/equities.png "equities")

- Bonds
![bonds](https://github.com/gcedism/portfolio/blob/main/docs/bonds.png "bonds")


### US Zero Curve calculation :

- Calculates using bootstrapp from US Treasury curves
- Using Deposits and Treasury

### Options

![Options Greek management](https://github.com/gcedism/portfolio/blob/main/docs/options%20port.png "Options")




