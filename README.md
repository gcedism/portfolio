# <span style="color:darkblue">Financial Portfolio</span>
---

## IMPLEMENTED : Newton-Rhapson for BOND SPREAD calculation

### Portfolio of financial securities with features that include :

- Snapshot with positions with current value
- Breakdown of assets in Asset Classes / Currencies
- Performance with a given window
- Risk measures : v@r for now
- Performance Attribution for different Asset Classes
- Cash Flow projection

### Securities files implement different Calculations for all Securities : 

- Bonds
- Equities
- Funds

### Inputs
Portfolio needs to received some pricing feeder for the securities and a Blotter containing all trades executed


### US Zero Curve calculation :

- Calculates using bootstrapp from US Treasury curves only
- To be implemented using swaps and Eurodollar
- Missing source for US Treasury curve 

### Some screenshots : 

![Performance Attribution](https://github.com/gcedism/portfolio/blob/main/fig/Screenshot%202022-11-04%20at%2008.19.11.png "Performance Attribution")

Total Performance

![Performance](https://github.com/gcedism/portfolio/blob/main/fig/Screenshot%202022-11-04%20at%2008.19.24.png "Performance")

