import matplotlib.pyplot as plt


class basic_plot:
  '''
  Defines a Basic Plotting Style
  '''

  def __init__(self, **kwargs):
    self._source = kwargs['source'] if 'source' in kwargs else 'No Source'
    self._save = kwargs['save'] if 'save' in kwargs else None

    print('Basic Plot')

  def __call__(self, _func):

    def wrapper(*args, **kwargs):
      f, ax = _func(*args, **kwargs)
      ax.spines[['right', 'top']].set_visible(False)
      ax.grid(alpha=0.5, ls='--')
      ax.text(0,
              -0.1,
              'Source : ' + self._source,
              fontstyle='italic',
              transform=ax.transAxes)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=12)
      if self._save: plt.savefig(self._save)
      plt.show()

    return wrapper
