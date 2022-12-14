from IPython.display import display_html
from .portfolio import Portfolio

FOLDER = __file__[:-len('reporting.py')]

def OptionsReport(port:Portfolio) :
    tpl = ""
    with open(FOLDER + 'reports/options.html') as f:
        tpl = f.read()
        f.close()
        
    tpl = tpl.replace('{{mainTitle}}', 'Options Report')
    tpl = tpl.replace('{{optionsDelta}}', "{:,.2f}".format(port._options._totalDelta))
    tpl = tpl.replace('{{portDelta}}', "{:,.2f}".format(port._assets.loc['option', 'amount']))
    tpl = tpl.replace('{{totalDelta$}}', "{:,.2f}".format(port._assets.loc['option', 'amount'] + port._options._totalDelta))
    tpl = tpl.replace('{{totalDelta%}}', "{:,.2f}".format((port._assets.loc['option', 'amount'] + port._options._totalDelta) / port._assets['amount'].sum()))
    tpl = tpl.replace('{{gamma}}', "{:,.2f}".format(port._options._totalGamma))
    tpl = tpl.replace('{{theta}}', "{:,.2f}".format(port._options._totalTheta))
    tpl = tpl.replace('{{mtm}}', "{:,.2f}".format(port._options._mtm))
    tpl = tpl.replace('{{gammaUpMatrix}}', port._options.gammaUpMatrix.to_html())
    tpl = tpl.replace('{{gammaDownMatrix}}', port._options.gammaDownMatrix.to_html())
    
    with open(FOLDER + 'reports/optionsToday.html', 'w', encoding='utf-8') as f:
        f.write(tpl)
        
    display_html(tpl, raw=True)
    
    