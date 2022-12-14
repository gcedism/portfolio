import pandas as pd
import numpy as np

from IPython.display import display_html
from itertools import chain,cycle
    
def display_side_by_side(*args):
    html_str=''
    for df in args:
        html_str+='<th style="text-align:center"><td style="vertical-align:top">'
        html_str+=df.to_html().replace('table','table style="display:inline"')
        html_str+='</td></th>'
    display_html(html_str, raw=True)

#Not Working on Jupyter 3.11 +
def display_side_by_side_title(*args, titles=cycle([''])):
    html_str=''
    for df, title in zip(args, chain(titles, cycle(['</br>'])) ):
        html_str+='<th style="text-align:center"><td style="vertical-align:top">'
        html_str+=f'<h2 style="text-align: center;">{title}</h2>'
        html_str+=df.to_html().replace('table','table style="display:inline"')
        html_str+='</td></th>'
    display_html(html_str, raw=True)
    
def interpolate(coord:tuple, table:pd.DataFrame) -> float :
    _table = table.copy()
    _table.loc[coord[0], coord[1]] = np.NaN
    _table = _table[sorted(_table.columns)].sort_index().interpolate(axis=0).interpolate(axis=1)
    
    return _table.loc[coord[0], coord[1]]