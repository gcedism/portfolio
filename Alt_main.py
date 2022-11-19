import numpy as np
import matplotlib.pyplot as plt
from Plotting import Basic_plot

x = np.arange(10)
y = np.random.rand(10)


@Basic_plot(source='Source', save='fig.jpg')
def plot(*args, **kwargs):
  f, ax = plt.subplots(figsize=(5, 5))
  ax.plot(x, y, lw=3, label='Test')
  return f, ax


plot(x, y)
