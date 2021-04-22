import os
import itertools
import collections
import pprint
import numpy as np
import pandas as pd
from scipy import stats as sps
from scipy.interpolate import interp1d
from datetime import datetime
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib.dates as mdates
from matplotlib.dates import date2num, num2date
from matplotlib.backends.backend_pgf import FigureCanvasPgf
from matplotlib.colors import ListedColormap

from scipy.interpolate import griddata
import matplotlib.colors as colors


from lib.rt import compute_daily_rts, R_T_RANGE
import lib.rt_nbinom
from lib.summary import *

TO_HOURS = 24.0
DPI = 200
NO_PLOT = False
TEST_LAG = 48.0 # hours

LINE_WIDTH = 7.0
COL_WIDTH = 3.333

FIG_SIZE_TRIPLE = (COL_WIDTH / 3, COL_WIDTH / 3 * 4/6)
FIG_SIZE_TRIPLE_TALL = (COL_WIDTH / 3, COL_WIDTH / 3 * 5/6)

FIG_SIZE_DOUBLE = (COL_WIDTH / 2, COL_WIDTH / 2 * 4/6)
FIG_SIZE_DOUBLE_TALL = (COL_WIDTH / 2, COL_WIDTH / 2 * 5/6)

CUSTOM_FIG_SIZE_FULL_PAGE_TRIPLE = (LINE_WIDTH / 3, COL_WIDTH / 2 * 5/6)

FIG_SIZE_FULL_PAGE_TRIPLE = (LINE_WIDTH / 3, LINE_WIDTH / 3 * 4/6)
FIG_SIZE_FULL_PAGE_TRIPLE_TALL = (LINE_WIDTH / 3, LINE_WIDTH / 3 * 5/6)
FIG_SIZE_FULL_PAGE_DOUBLE_ARXIV = (LINE_WIDTH / 2, LINE_WIDTH / 3 * 4/6) # 2
FIG_SIZE_FULL_PAGE_DOUBLE_ARXIV_TALL = (LINE_WIDTH / 2, LINE_WIDTH / 3 * 4.5/6) # 2 tall
FIG_SIZE_FULL_PAGE_TRIPLE_ARXIV = (LINE_WIDTH / 3.3, LINE_WIDTH / 3 * 3.5/6) # 4x3 full page
FIG_SIZE_FULL_PAGE_TRIPLE_ARXIV_SMALL = (LINE_WIDTH / 3.7, LINE_WIDTH / 3 * 2.5/6) # 6x4 full page
CUSTOM_FIG_SIZE_FULL_PAGE_QUAD = (LINE_WIDTH / 4, COL_WIDTH / 2 * 5/6)

SIGCONF_RCPARAMS_DOUBLE = {
    # Fig params
    "figure.autolayout": True,          # Makes sure nothing the feature is neat & tight.
    "figure.figsize": FIG_SIZE_DOUBLE,  # Column width: 3.333 in, space between cols: 0.333 in.
    "figure.dpi": 150,                  # Displays figures nicely in notebooks.
    # Axes params
    "axes.linewidth": 0.5,              # Matplotlib's current default is 0.8.
    "hatch.linewidth": 0.3,
    "xtick.major.width": 0.5,
    "xtick.minor.width": 0.5,
    'xtick.major.pad': 1.0,
    'xtick.major.size': 1.75,
    'xtick.minor.pad': 1.0,
    'xtick.minor.size': 1.0,
    "ytick.major.width": 0.5,
    "ytick.minor.width": 0.5,
    'ytick.major.pad': 1.0,
    'ytick.major.size': 1.75,
    'ytick.minor.pad': 1.0,
    'ytick.minor.size': 1.0,
    "axes.labelpad": 0.5,
    # Plot params
    "lines.linewidth": 0.8,              # Width of lines
    "lines.markeredgewidth": 0.3,
    # Legend params
    "legend.fontsize": 8.5,        # Make the legend/label fonts a little smaller
    "legend.frameon": True,              # Remove the black frame around the legend
    "legend.handletextpad": 0.3,
    "legend.borderaxespad": 0.2,
    "legend.labelspacing": 0.1,
    "patch.linewidth": 0.5,
    # Font params
    "text.usetex": True,                 # use LaTeX to write all text
    "font.family": "serif",              # use serif rather than sans-serif
    "font.serif": "Linux Libertine O",   # use "Linux Libertine" as the standard font
    "font.size": 9,
    "axes.titlesize": 8,          # LaTeX default is 10pt font.
    "axes.labelsize": 8,          # LaTeX default is 10pt font.
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    # PDF settings
    "pgf.texsystem": "xelatex",         # Use Xelatex which is TTF font aware
    "pgf.rcfonts": False,               # Use pgf.preamble, ignore standard Matplotlib RC
    "pgf.preamble": [
        r'\usepackage{fontspec}',
        r'\usepackage{unicode-math}',
        r'\usepackage{libertine}',
        r'\setmainfont{Linux Libertine O}',
        r'\setmathfont{Linux Libertine O}',
    ]
}

SIGCONF_RCPARAMS_TRIPLE = {
    # Fig params
    "figure.autolayout": True,          # Makes sure nothing the feature is neat & tight.
    "figure.figsize": FIG_SIZE_TRIPLE,  # Column width: 3.333 in, space between cols: 0.333 in.
    "figure.dpi": 150,                  # Displays figures nicely in notebooks.
    # Axes params
    "axes.linewidth": 0.4,              # Matplotlib's current default is 0.8.
    "hatch.linewidth": 0.3,
    "xtick.major.width": 0.4,
    "xtick.minor.width": 0.4,
    'xtick.major.pad': 1.0,
    'xtick.major.size': 1.75,
    'xtick.minor.pad': 1.0,
    'xtick.minor.size': 1.0,
    "ytick.major.width": 0.4,
    "ytick.minor.width": 0.4,
    'ytick.major.pad': 1.0,
    'ytick.major.size': 1.75,
    'ytick.minor.pad': 1.0,
    'ytick.minor.size': 1.0,
    "axes.labelpad": 0.5,
    # Plot params
    "lines.linewidth": 0.8,              # Width of lines
    "lines.markeredgewidth": 0.3,
    # Legend
    "legend.fontsize": 5.5,              # Make the legend/label fonts a little smaller
    "legend.frameon": True,              # Remove the black frame around the legend
    "legend.handletextpad": 0.5,
    "legend.borderaxespad": 0.0,
    "legend.labelspacing": 0.05,
    "patch.linewidth": 0.3,
    # Font params
    "text.usetex": True,                 # use LaTeX to write all text
    "font.family": "serif",              # use serif rather than sans-serif
    "font.serif": "Linux Libertine O",   # use "Linux Libertine" as the standard font
    "font.size": 6,
    "axes.titlesize": 5,                 # LaTeX default is 10pt font.
    "axes.labelsize": 5,                 # LaTeX default is 10pt font.
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
    # PDF settings
    "pgf.texsystem": "xelatex",          # Use Xelatex which is TTF font aware
    "pgf.rcfonts": False,                # Use pgf.preamble, ignore standard Matplotlib RC
    "pgf.preamble": [
        r'\usepackage{fontspec}',
        r'\usepackage{unicode-math}',
        r'\usepackage{libertine}',
        r'\setmainfont{Linux Libertine O}',
        r'\setmathfont{Linux Libertine O}',
    ]
}

NEURIPS_LINE_WIDTH = 5.5  # Text width: 5.5in (double figure minus spacing 0.2in).
FIG_SIZE_NEURIPS_DOUBLE = (NEURIPS_LINE_WIDTH / 2, NEURIPS_LINE_WIDTH / 2 * 4/6)
FIG_SIZE_NEURIPS_TRIPLE = (NEURIPS_LINE_WIDTH / 3, NEURIPS_LINE_WIDTH / 3 * 4/6)
FIG_SIZE_NEURIPS_DOUBLE_TALL = (NEURIPS_LINE_WIDTH / 2, NEURIPS_LINE_WIDTH / 2 * 5/6)
FIG_SIZE_NEURIPS_TRIPLE_TALL = (NEURIPS_LINE_WIDTH / 3, NEURIPS_LINE_WIDTH / 3 * 5/6)

NEURIPS_RCPARAMS = {
    "figure.autolayout": False,         # Makes sure nothing the feature is neat & tight.
    "figure.figsize": FIG_SIZE_NEURIPS_DOUBLE,
    "figure.dpi": 150,                  # Displays figures nicely in notebooks.
    # Axes params
    "axes.linewidth": 0.5,              # Matplotlib's current default is 0.8.
    "xtick.major.width": 0.5,
    "xtick.minor.width": 0.5,
    "ytick.major.width": 0.5,
    "ytick.minor.width": 0.5,

    "hatch.linewidth": 0.3,
    "xtick.major.width": 0.5,
    "xtick.minor.width": 0.5,
    'xtick.major.pad': 1.0,
    'xtick.major.size': 1.75,
    'xtick.minor.pad': 1.0,
    'xtick.minor.size': 1.0,

    'ytick.major.pad': 1.0,
    'ytick.major.size': 1.75,
    'ytick.minor.pad': 1.0,
    'ytick.minor.size': 1.0,

    "axes.labelpad": 0.5,
    # Grid
    "grid.linewidth": 0.3,
    # Plot params
    "lines.linewidth": 1.0,
    "lines.markersize": 4,
    'errorbar.capsize': 3.0,
    # Font
    "text.usetex": True,                # use LaTeX to write all text
    "font.family": "serif",             # use serif rather than sans-serif
    #"font.serif": "Times New Roman",    # use "Times New Roman" as the standard font
    "font.size": 8.5,
    "axes.titlesize": 8.5,                # LaTeX default is 10pt font.
    "axes.labelsize": 8.5,                # LaTeX default is 10pt font.
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    # Legend
    "legend.fontsize": 7,        # Make the legend/label fonts a little smaller
    "legend.frameon": True,              # Remove the black frame around the legend
    "legend.handletextpad": 0.3,
    "legend.borderaxespad": 0.2,
    "legend.labelspacing": 0.1,
    "patch.linewidth": 0.5,
    # PDF
    "pgf.texsystem": "xelatex",         # use Xelatex which is TTF font aware
    "pgf.rcfonts": False,               # Use pgf.preamble, ignore standard Matplotlib RC
    "pgf.preamble": [
        r'\usepackage{fontspec}',
        r'\usepackage{unicode-math}',
        #r'\setmainfont{Times New Roman}',
    ],
}



def trans_data_to_axis(ax):
    """Compute the transform from data to axis coordinate system in axis `ax`"""
    axis_to_data = ax.transAxes + ax.transData.inverted()
    data_to_axis = axis_to_data.inverted()
    return data_to_axis

def days_to_datetime(arr, start_date):
    # timestamps
    ts = arr * 24 * 60 * 60 + pd.Timestamp(start_date).timestamp()
    return pd.to_datetime(ts, unit='s')


def lockdown_widget(ax, lockdown_at, start_date, lockdown_label_y, lockdown_label='Lockdown',
                    xshift=0.0, zorder=None, ls='--', color='black', text_off=False):
    """
    Draw the lockdown widget corresponding to a vertical line at the desired location along with a
    label. The data can be passed either in `float` or in `datetime` format.

    Parameters
    ----------
    ax
        Axis to draw on
    lockdown_at
        Location of vertical lockdown line
    start_date
        Value of the origin of the x-axis
    lockdown_label_y
        Location of the text label on the y-axis
    lockdown_label : str (optional, default: 'Lockdown')
        Text label
    xshift : float (optional, default: 0.0)
        Shift in a-axis of the text label
    zorder : int (optional, default: None)
        z-order of the widget
    ls : str (optional, default: '--')
        Linestyle of the vertical line
    color : str (optional, default: 'black')
        color of the vertical line
    text_off : bool (optional, default: False)
        Indicate if the text label should be turned off
    """
    if isinstance(start_date, float):  # If plot with float x-axis
        lckdn_x = start_date + lockdown_at
        ax.axvline(lckdn_x, linestyle=ls, color=color, label='_nolegend_',
                   zorder=zorder)
    else:
        # If plot with datetime x-axis
        lckdn_dt = days_to_datetime(lockdown_at, start_date=start_date)  # str to datetime
        lckdn_x_d = lckdn_dt.toordinal()  # datetime to float in data coordinates
        ax.axvline(lckdn_x_d, linestyle=ls, color=color, label='_nolegend_',
                   zorder=zorder)
        # Display the text label
        if not text_off:
            if xshift == 0.0:
                # Automatic shift of the text in the plot (normalized) axis coordinates
                lckdn_x_a, _ = trans_data_to_axis(ax).transform([lckdn_x_d, 0.0])  # data coordinates to axis coordinates
                ax.text(x=lckdn_x_a, y=lockdown_label_y, s=lockdown_label,
                        transform=ax.transAxes, rotation=90,
                        verticalalignment='bottom',
                        horizontalalignment='right')
            else:
                # NOTE: for backward-compatibility, manual shift of the text, should be removed
                ax.text(x=lckdn_dt + pd.Timedelta(xshift, unit='d'),
                        y=lockdown_label_y, s=lockdown_label, rotation=90)

def target_widget(show_target,start_date, ax, zorder=None, ms=4.0, label='COVID-19 case data'):
    txx = np.linspace(0, show_target.shape[0] - 1, num=show_target.shape[0])
    txx = days_to_datetime(txx, start_date=start_date)
    ax.plot(txx, show_target, ls='', marker='x', ms=ms,
            color='black', label=label, zorder=zorder)


class CustomSitesProportionFixedLocator(plt.Locator):
    """
    Custom locator to avoid tick font bug of matplotlib
    """

    def __init__(self):
        pass

    def __call__(self):
        return np.log(np.array([2, 5, 10, 25, 100]))


class Plotter(object):
    """
    Plotting class
    """

    def __init__(self):

        # plot constants
        # check out https://colorhunt.co/

        self.color_expo = '#ffcc00'
        self.color_iasy = '#00a8cc'
        self.color_ipre = '#005082'
        self.color_isym = '#000839'

        self.color_testing = '#ffa41b'

        self.color_posi = '#4daf4a'
        self.color_nega = '#e41a1c'

        self.color_all = '#ffa41b'
        self.color_positive = '#00a8cc'
        self.color_age = '#005082'
        self.color_tracing = '#000839'

        self.color_infected = '#000839'

        self.filling_alpha = 0.2

        self.color_different_scenarios = [
            '#e41a1c',
            '#377eb8',
            '#4daf4a',
            '#984ea3',
            '#ff7f00',
            '#ffff33',
            '#a65628',
            '#f781bf',
            '#999999'
        ]

        self.color_different_scenarios_alt = [
            '#a1dab4',
            '#41b6c4',
            '#2c7fb8',
            '#253494',
        ]

        # 2D visualization
        self.density_alpha = 0.7

        self.marker_home = "^"
        self.marker_site = "o"

        self.color_home = '#000839'
        self.color_site = '#000000'

        self.size_home = 80
        self.size_site = 300

    def _set_matplotlib_params(self, format='dobule'):
        matplotlib.backend_bases.register_backend('pdf', FigureCanvasPgf)
        if format == 'double':
            plt.rcParams.update(SIGCONF_RCPARAMS_DOUBLE)
        elif format == 'triple':
            plt.rcParams.update(SIGCONF_RCPARAMS_TRIPLE)
        if format == 'neurips-double':
            plt.rcParams.update(NEURIPS_RCPARAMS)
        else:
            raise ValueError('Invalid figure format.')

    def _set_default_axis_settings(self, ax):
        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

    def plot_cumulative_infected(self, sim, title='Example', filename='daily_inf_0',
                                 figsize=(6, 5), errorevery=20, acc=1000, ymax=None,
                                 lockdown_label='Lockdown', lockdown_at=None,
                                 lockdown_label_y=None, show_target=None,
                                 start_date='1970-01-01',
                                 subplot_adjust=None, legend_loc='upper right'):
        ''''
        Plots daily infected split by group
        averaged over random restarts, using error bars for std-dev
        '''

        if acc > sim.max_time:
            acc = int(sim.max_time)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        ts, iasy_mu, iasy_sig = self.__comp_state_cumulative(sim, 'iasy', acc)
        # _,  ipre_mu, ipre_sig = self.__comp_state_cumulative(sim, 'ipre', acc)
        _,  isym_mu, isym_sig = self.__comp_state_cumulative(sim, 'isym', acc)
        # _,  expo_mu, iexpo_sig = self.__comp_state_cumulative(sim, 'expo', acc)
        # _,  posi_mu, posi_sig = self.__comp_state_cumulative(sim, 'posi', acc)

        line_xaxis = np.zeros(ts.shape)
        line_iasy = iasy_mu
        line_isym = iasy_mu + isym_mu

        error_isym = np.sqrt(iasy_sig**2 + isym_sig**2)

        # Convert x-axis into posix timestamps and use pandas to plot as dates
        ts = days_to_datetime(ts, start_date=start_date)

        # lines
        ax.plot(ts, line_iasy, c='black', linestyle='-')
        ax.errorbar(ts, line_isym, yerr=error_isym, c='black', linestyle='-',
                    elinewidth=0.8, errorevery=errorevery, capsize=3.0)

        # filling
        ax.fill_between(ts, line_xaxis, line_iasy, alpha=self.filling_alpha, label='Asymptomatic',
                        edgecolor=self.color_iasy, facecolor=self.color_iasy, linewidth=0, zorder=0)
        ax.fill_between(ts, line_iasy, line_isym, alpha=self.filling_alpha, label='Symptomatic',
                        edgecolor=self.color_isym, facecolor=self.color_isym, linewidth=0, zorder=0)

        # limits
        if ymax is None:
            ymax = 1.5 * np.max(iasy_mu + isym_mu)
        ax.set_ylim((0, ymax))

        # ax.set_xlabel('Days')
        ax.set_ylabel('People')

        # extra
        if lockdown_at is not None:
            lockdown_widget(ax, lockdown_at, start_date,
                            lockdown_label_y,
                            lockdown_label)
        if show_target is not None:
            target_widget(show_target, start_date, ax)

        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

        #set ticks every week
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        #set major ticks format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')

        # legend
        ax.legend(loc=legend_loc, borderaxespad=0.5)

        subplot_adjust = subplot_adjust or {'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.draw()

        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return

    def plot_daily_infected(self, sim, title='Example', filename='daily_inf_0',
                            figsize=(6, 5), errorevery=20, acc=1000, ymax=None,
                            lockdown_label='Lockdown', lockdown_at=None,
                            lockdown_label_y=None, show_target=None,
                            lockdown_end=None,
                            start_date='1970-01-01',
                            subplot_adjust=None, legend_loc='upper right'):
        ''''
        Plots daily infected split by group
        averaged over random restarts, using error bars for std-dev
        '''

        if acc > sim.max_time:
            acc = int(sim.max_time)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        ts, iasy_mu, iasy_sig = comp_state_over_time(sim, 'iasy', acc)
        _,  ipre_mu, ipre_sig = comp_state_over_time(sim, 'ipre', acc)
        _,  isym_mu, isym_sig = comp_state_over_time(sim, 'isym', acc)
        # _,  expo_mu, iexpo_sig = comp_state_over_time(sim, 'expo', acc)
        # _,  posi_mu, posi_sig = comp_state_over_time(sim, 'posi', acc)

        line_xaxis = np.zeros(ts.shape)
        line_iasy = iasy_mu
        line_ipre = iasy_mu + ipre_mu
        line_isym = iasy_mu + ipre_mu + isym_mu
        error_isym = np.sqrt(iasy_sig**2 + ipre_sig**2 + isym_sig**2)

        # Convert x-axis into posix timestamps and use pandas to plot as dates
        ts = days_to_datetime(ts, start_date=start_date)

        # lines
        ax.plot(ts, line_iasy,
                c='black', linestyle='-')
        ax.plot(ts, line_ipre,
                c='black', linestyle='-')
        ax.errorbar(ts, line_isym, yerr=error_isym, c='black', linestyle='-',
                    elinewidth=0.8, errorevery=errorevery, capsize=3.0)

        # filling
        ax.fill_between(ts, line_xaxis, line_iasy, alpha=0.5, label='Asymptomatic',
                        edgecolor=self.color_iasy, facecolor=self.color_iasy, linewidth=0, zorder=0)
        ax.fill_between(ts, line_iasy, line_ipre, alpha=0.5, label='Pre-symptomatic',
                        edgecolor=self.color_ipre, facecolor=self.color_ipre, linewidth=0, zorder=0)
        ax.fill_between(ts, line_ipre, line_isym, alpha=0.5, label='Symptomatic',
                        edgecolor=self.color_isym, facecolor=self.color_isym, linewidth=0, zorder=0)

        # limits
        if ymax is None:
            ymax = 1.5 * np.max(iasy_mu + ipre_mu + isym_mu)
        ax.set_ylim((0, ymax))

        # ax.set_xlabel('Days')
        ax.set_ylabel('People')

        # extra
        if lockdown_at is not None:
            lockdown_widget(ax, lockdown_at, start_date,
                            lockdown_label_y,
                            lockdown_label)
        if lockdown_end is not None:
            lockdown_widget(ax=ax, lockdown_at=lockdown_end, start_date=start_date,
                            lockdown_label_y=lockdown_label_y,
                            lockdown_label='End of lockdown', ls='dotted')
        if show_target is not None:
            target_widget(show_target, start_date, ax)


        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

        #set ticks every week
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        #set major ticks format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')

        # legend
        ax.legend(loc=legend_loc, borderaxespad=0.5)

        subplot_adjust = subplot_adjust or {'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.draw()

        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return

    def plot_daily_tested(self, sim, title='Example', filename='daily_tested_0', figsize=(10, 10), errorevery=20,
        acc=1000, ymax=None):

        ''''
        Plots daily tested, positive daily tested, negative daily tested
        averaged over random restarts, using error bars for std-dev
        '''

        if acc > sim.max_time:
            acc = int(sim.max_time)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        # automatically shifted by `test_lag` in the function
        ts, posi_mu, posi_sig = comp_state_over_time(sim, 'posi', acc)
        _,  nega_mu, nega_sig = comp_state_over_time(sim, 'nega', acc)

        line_xaxis = np.zeros(ts.shape)
        line_posi = posi_mu
        line_nega = posi_mu + nega_mu

        error_posi = posi_sig
        error_nega = nega_sig + posi_sig

        T = posi_mu.shape[0]

        # lines
        ax.errorbar(ts, line_posi, yerr=posi_sig, elinewidth=0.8, errorevery=errorevery,
                c='black', linestyle='dotted')
        ax.errorbar(ts, line_nega, yerr=nega_sig, elinewidth=0.8, errorevery=errorevery,
                c='black', linestyle='-')

        # filling
        ax.fill_between(ts, line_xaxis, line_posi, alpha=0.5, label=r'Positive tests',
                        edgecolor=self.color_posi, facecolor=self.color_posi, linewidth=0, zorder=0)
        ax.fill_between(ts, line_posi, line_nega, alpha=0.5, label=r'Negative tests',
                        edgecolor=self.color_nega, facecolor=self.color_nega, linewidth=0, zorder=0)
        # axis
        ax.set_xlim((0, np.max(ts)))
        if ymax is None:
            ymax = 1.5 * np.max(posi_mu + nega_mu)
        ax.set_ylim((0, ymax))

        ax.set_xlabel(r'$t$ [days]')
        ax.set_ylabel(r'Tests')

        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

        # legend
        fig.legend(loc='center right', borderaxespad=0.1)
        # Adjust the scaling factor to fit your legend text completely outside the plot
        plt.subplots_adjust(right=0.70)
        ax.set_title(title, pad=20)
        plt.draw()
        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI, bbox_inches='tight')
        if NO_PLOT:
            plt.close()
        return

    def plot_daily_at_home(self, sim, title='Example', filename='daily_at_home_0', figsize=(10, 10), errorevery=20, acc=1000, ymax=None):

        ''''
        Plots daily tested, positive daily tested, negative daily tested
        averaged over random restarts, using error bars for std-dev
        '''

        if acc > sim.max_time:
            acc = int(sim.max_time)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        ts, all_mu, all_sig = comp_contained_over_time(sim, 'SocialDistancingForAllMeasure', acc)
        _,  positive_mu, positive_sig = comp_contained_over_time(sim, 'SocialDistancingForPositiveMeasure', acc)
        _,  age_mu, age_sig = comp_contained_over_time(sim, 'SocialDistancingByAgeMeasure', acc)
        _,  tracing_mu, tracing_sig = comp_contained_over_time(sim, 'SocialDistancingForSmartTracing', acc)

        _, iasy_mu, iasy_sig = comp_state_over_time(sim, 'iasy', acc)
        _,  ipre_mu, ipre_sig = comp_state_over_time(sim, 'ipre', acc)
        _,  isym_mu, isym_sig = comp_state_over_time(sim, 'isym', acc)

        line_xaxis = np.zeros(ts.shape)

        line_all = all_mu
        line_positive = positive_mu
        line_age = age_mu
        line_tracing = tracing_mu

        line_infected = iasy_mu + ipre_mu + isym_mu

        error_all = all_sig
        error_positive = positive_sig
        error_age = age_sig
        error_tracing = tracing_sig

        error_infected = np.sqrt(np.square(iasy_sig) + np.square(ipre_sig) + np.square(isym_sig))

        # lines
        ax.errorbar(ts, line_infected, label=r'Total infected', errorevery=errorevery, c=self.color_infected, linestyle='--', yerr=error_infected)

        ax.errorbar(ts, line_all, yerr=error_all, elinewidth=0.8, errorevery=errorevery,
                c='black', linestyle='-')
        ax.errorbar(ts, line_positive, yerr=error_positive, elinewidth=0.8, errorevery=errorevery,
                c='black', linestyle='-')
        ax.errorbar(ts, line_age, yerr=error_age, elinewidth=0.8, errorevery=errorevery,
                c='black', linestyle='-')
        ax.errorbar(ts, line_tracing, yerr=error_tracing, elinewidth=0.8, errorevery=errorevery,
                c='black', linestyle='-')

        # filling
        ax.fill_between(ts, line_xaxis, line_all, alpha=self.filling_alpha, label=r'SD for all',
                        edgecolor=self.color_all, facecolor=self.color_all, linewidth=0, zorder=0)
        ax.fill_between(ts, line_xaxis, line_positive, alpha=self.filling_alpha, label=r'SD for positively tested',
                        edgecolor=self.color_positive, facecolor=self.color_positive, linewidth=0, zorder=0)
        ax.fill_between(ts, line_xaxis, line_age, alpha=self.filling_alpha, label=r'SD for age group',
                        edgecolor=self.color_age, facecolor=self.color_age, linewidth=0, zorder=0)
        ax.fill_between(ts, line_xaxis, line_tracing, alpha=self.filling_alpha, label=r'SD for traced contacts',
                        edgecolor=self.color_tracing, facecolor=self.color_tracing, linewidth=0, zorder=0)

        # axis
        ax.set_xlim((0, np.max(ts)))
        if ymax is None:
            ymax = 1.5 * np.max([all_mu, positive_mu, age_mu, tracing_mu])
        ax.set_ylim((0, ymax))

        ax.set_xlabel(r'$t$ [days]')
        ax.set_ylabel(r'[people]')

        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

        # legend
        fig.legend(loc='center right', borderaxespad=0.1)
        # Adjust the scaling factor to fit your legend text completely outside the plot
        plt.subplots_adjust(right=0.70)
        ax.set_title(title, pad=20)
        plt.draw()
        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI, bbox_inches='tight')
        if NO_PLOT:
            plt.close()
        return

    def compare_total_infections(self, sims, titles, figtitle='Title', figformat='double',
        filename='compare_inf_0', figsize=None, errorevery=20, acc=500, ymax=None, x_axis_dates=True,
        lockdown_label='Lockdown', lockdown_at=None, lockdown_label_y=None, lockdown_xshift=0.0,
        conditional_measures=None,
        show_positives=False, show_legend=True, legend_is_left=False,
        subplot_adjust=None, start_date='1970-01-01', xtick_interval=2, first_one_dashed=False,
        show_single_runs=False, which_single_runs=None):
        ''''
        Plots total infections for each simulation, named as provided by `titles`
        to compare different measures/interventions taken. Colors taken as defined in __init__, and
        averaged over random restarts, using error bars for std-dev
        '''

        assert isinstance(sims[0], str), '`sims` must be list of filepaths'

        # Set double figure format
        self._set_matplotlib_params(format=figformat)
        # Draw figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        for i, sim in enumerate(sims):
            is_conditional = True if i == conditional_measures else False
            try:
                data = load_condensed_summary(sim, acc)
            except FileNotFoundError:
                acc = create_condensed_summary_from_path(sim, acc=acc)
                data = load_condensed_summary(sim, acc)

            ts = data['ts']
            lockdown_at = data['lockdowns'] if is_conditional else lockdown_at
            if x_axis_dates:
                # Convert x-axis into posix timestamps and use pandas to plot as dates
                ts = days_to_datetime(ts, start_date=start_date)

            if not show_single_runs:
                iasy_mu = data['iasy_mu']
                iasy_sig = data['iasy_sig']
                ipre_mu = data['ipre_mu']
                ipre_sig = data['ipre_sig']
                isym_mu = data['isym_mu']
                isym_sig = data['isym_sig']

                line_infected = iasy_mu + ipre_mu + isym_mu
                error_infected = np.sqrt(np.square(iasy_sig) + np.square(ipre_sig) + np.square(isym_sig))

                # lines
                ax.plot(ts, line_infected, linestyle='-', label=titles[i], c=self.color_different_scenarios[i])
                ax.fill_between(ts, np.maximum(line_infected - 2 * error_infected, 0), line_infected + 2 * error_infected,
                                color=self.color_different_scenarios[i], alpha=self.filling_alpha, linewidth=0.0)
            else:
                iasy = data['iasy']
                ipre = data['ipre']
                isym = data['isym']

                lines_infected = iasy + ipre + isym

                # lines
                runs = [which_single_runs] if which_single_runs else range(min(show_single_runs, sim.random_repeats))
                for k, r in enumerate(runs):
                    ax.plot(ts, lines_infected[:, r], linestyle='-', label=titles[i] if k == 0 else None,
                            c=self.color_different_scenarios[i])

                    # For conditional measures only
                    if lockdown_at:
                        for lockdown in lockdown_at[r]:
                            start_lockdown = lockdown[0] / TO_HOURS
                            end_lockdown = lockdown[1] / TO_HOURS
                            lockdown_widget(ax, start_lockdown, 0.0,
                                            lockdown_label_y,
                                            None)
                            lockdown_widget(ax, end_lockdown, 0.0,
                                            lockdown_label_y,
                                            None, ls='-')

        # axis
        ax.set_xlim(left=np.min(ts))
        if ymax is None:
            ymax = 1.5 * np.max(iasy_mu + ipre_mu + isym_mu)
        ax.set_ylim((0, ymax))

        # ax.set_xlabel('Days')
        if x_axis_dates:
            # set xticks every week
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=1, interval=1))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=1, interval=xtick_interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        else:
            ax.set_xlabel(r'$t$ [days]')

        ax.set_ylabel('Infected')

        if not isinstance(lockdown_at, list):
            if lockdown_at is not None:
                lockdown_widget(ax, lockdown_at, start_date,
                                lockdown_label_y,
                                lockdown_label,
                                xshift=lockdown_xshift)

        # Set default axes style
        self._set_default_axis_settings(ax=ax)

        if show_legend:
            # legend
            if legend_is_left:
                leg = ax.legend(loc='upper left',
                          bbox_to_anchor=(0.001, 0.999),
                          bbox_transform=ax.transAxes,
                        #   prop={'size': 5.6}
                          )
            else:
                leg = ax.legend(loc='upper right',
                          bbox_to_anchor=(0.999, 0.999),
                          bbox_transform=ax.transAxes,
                        #   prop={'size': 5.6}
                          )

        subplot_adjust = subplot_adjust or {'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return

    def compare_quantity(self, sims, titles, quantity='infected', mode='total', ymax=None,
                         normalization_baseline_path=None,
                         start_date='1970-01-01', xtick_interval=3, x_axis_dates=False,
                         figformat='double', filename='compare_epidemics', figsize=None,
                         lockdown_label='Lockdown', lockdown_at=None, lockdown_label_y=None, lockdown_xshift=0.0,
                         show_legend=True, legend_is_left=False, subplot_adjust=None):
        ''''
        Plots `quantity` in `mode` for each simulation, named as provided by `titles`
        to compare different measures/interventions taken. Colors taken as defined in __init__, and
        averaged over random restarts, using error bars for std-dev
        '''

        assert isinstance(sims[0], str), '`sims` must be list of filepaths'
        assert mode in ['total', 'daily', 'cumulative']
        assert quantity in ['infected', 'hosp', 'dead']

        labeldict = {'total': {'infected': 'Infected',
                               'hosp': 'Hospitalized',
                               'dead': 'Fatalities'},
                     'cumulative': {'infected': 'Cumulative Infections',
                                    'hosp': 'Cumulative Hospitalizations',
                                    'dead': 'Cumulative Fatalities'},
                     'daily': {'infected': 'Daily Infections',
                               'hosp': 'Daily Hospitalizations',
                               'dead': 'Daily Fatalities'},
                     }

        # Set double figure format
        self._set_matplotlib_params(format=figformat)
        # Draw figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Load baseline data
        # if normalization_baseline_path:
        #     baseline_data = load_condensed_summary_compat(normalization_baseline_path)
        #     baseline_cases, _ = get_plot_data(baseline_data, quantity=quantity, mode=mode)

        for i, sim in enumerate(sims):
            data = load_condensed_summary_compat(sim)
            ts = data['ts'] if not x_axis_dates else days_to_datetime(data['ts'], start_date=start_date)

            line_cases, error_cases = get_plot_data(data, quantity=quantity, mode=mode)
            ylabel = labeldict[mode][quantity]

            # if normalization_baseline_path:
            #     line_cases = 1 - line_cases / baseline_cases
            #     error_cases = error_cases / baseline_cases
            #     line_cases = np.nan_to_num(line_cases, nan=0.0)
            #     error_cases = np.nan_to_num(error_cases, nan=0.0)
            #     ylabel = f'Reduction in ' + ylabel

            # lines
            ax.plot(ts, line_cases, linestyle='-', label=titles[i], c=self.color_different_scenarios[i])
            ax.fill_between(ts, np.maximum(line_cases - 2 * error_cases, 0), line_cases + 2 * error_cases,
                            color=self.color_different_scenarios[i], alpha=self.filling_alpha, linewidth=0.0)

        # axis
        ax.set_xlim(left=np.min(ts))
        if ymax is None:
            ymax = 1.5 * np.max(line_cases)
        ax.set_ylim((0, ymax))

        if x_axis_dates:
            # set xticks every week
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=1, interval=1))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=1, interval=xtick_interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        else:
            ax.set_xlabel(r'$t$ [days]')

        ax.set_ylabel(ylabel)

        if lockdown_at is not None:
            lockdown_widget(ax, lockdown_at, start_date,
                            lockdown_label_y,
                            lockdown_label,
                            xshift=lockdown_xshift)

        # Set default axes style
        self._set_default_axis_settings(ax=ax)

        if show_legend:
            # legend
            if legend_is_left:
                leg = ax.legend(loc='upper left',
                          bbox_to_anchor=(0.001, 0.999),
                          bbox_transform=ax.transAxes,
                        #   prop={'size': 5.6}
                          )
            else:
                leg = ax.legend(loc='upper right',
                          bbox_to_anchor=(0.999, 0.999),
                          bbox_transform=ax.transAxes,
                        #   prop={'size': 5.6}
                          )

        subplot_adjust = subplot_adjust or {'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return

    def compare_total_fatalities_and_hospitalizations(self, sims, titles, mode='show_both',
        figtitle=r'Hospitalizations and Fatalities',
        lockdown_label='Lockdown', lockdown_at=None, lockdown_label_y=None,
        figformat='neurips-double',
        xtick_interval=2, lockdown_xshift=0.0,
        filename='compare_inf_0', figsize=(10, 10), errorevery=20, acc=1000, ymax=None,
        show_legend=True, legendYoffset=0.0, legend_is_left=False, legendXoffset=0.0,
        subplot_adjust=None, start_date='1970-01-01', first_one_dashed=False):

        ''''
        Plots total fatalities and hospitalizations for each simulation, named as provided by `titles`
        to compare different measures/interventions taken. Colors taken as defined in __init__, and
        averaged over random restarts, using error bars for std-dev
        '''

        # Set double figure format
        self._set_matplotlib_params(format=figformat)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        # hospitalizations
        for i, sim in enumerate(sims):
            if isinstance(sim, str):
                try:
                    data = load_condensed_summary(sim, acc=acc)
                except FileNotFoundError:
                    acc = create_condensed_summary_from_path(sim, acc=acc)
                    data = load_condensed_summary(sim, acc=acc)

                acc = data['acc']
                ts = data['ts']
                hosp_mu = data['hosp_mu']
                hosp_sig = data['hosp_sig']
                dead_mu = data['dead_mu']
                dead_sig = data['dead_sig']
                loaded_extracted_data = True
            else:
                loaded_extracted_data = False

            if not loaded_extracted_data:
                if acc > sim.max_time:
                    acc = int(sim.max_time)

                ts, hosp_mu, hosp_sig = comp_state_over_time(sim, 'hosp', acc)
                ts, dead_mu, dead_sig = comp_state_over_time(sim, 'dead', acc)

            # Convert x-axis into posix timestamps and use pandas to plot as dates
            ts = days_to_datetime(ts, start_date=start_date)

            # lines
            # ax.errorbar(ts, hosp_mu, yerr=2*hosp_sig, label=titles[i], errorevery=errorevery,
            #             c=self.color_different_scenarios[i], linestyle='-', elinewidth=0.8, capsize=3.0)

            # ax.errorbar(ts, dead_mu, yerr=2*dead_sig, errorevery=errorevery,
            #             c=self.color_different_scenarios[i], linestyle='dotted', elinewidth=0.8, capsize=3.0)
            if mode == 'show_both' or mode == 'show_hosp_only':
                ax.plot(ts, hosp_mu, linestyle='-',
                        label=titles[i], c=self.color_different_scenarios[i])
                ax.fill_between(ts, hosp_mu - 2 * hosp_sig, hosp_mu + 2 * hosp_sig,
                                color=self.color_different_scenarios[i], alpha=self.filling_alpha, linewidth=0.0)

            if mode == 'show_both' or mode == 'show_dead_only':
                linestyle = '-' if mode == 'show_dead_only' else 'dotted'
                labels = titles[i] if mode == 'show_dead_only' else None
                ax.plot(ts, dead_mu, linestyle=linestyle,
                        label=labels, c=self.color_different_scenarios[i])
                ax.fill_between(ts, dead_mu - 2 * dead_sig, dead_mu + 2 * dead_sig,
                                color=self.color_different_scenarios[i], alpha=self.filling_alpha, linewidth=0.0)

        # axis
        ax.set_xlim(left=np.min(ts))
        if ymax is None:
            ymax = 1.5 * np.max(hosp_mu + hosp_sig)
        ax.set_ylim((0, ymax))

        # ax.set_xlabel('Days')
        ax.set_ylabel('People')

        if not isinstance(lockdown_at, list):
            if lockdown_at is not None:
                lockdown_widget(ax, lockdown_at, start_date,
                                lockdown_label_y,
                                lockdown_label,
                                xshift=lockdown_xshift)

        # ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=1, interval=1))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=1, interval=xtick_interval))
       

        #set major ticks format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')

        self._set_default_axis_settings(ax=ax)

        # legend
        if show_legend:
            # legend
            if legend_is_left:
                leg = ax.legend(loc='upper left', borderaxespad=0.5)
            else:
                leg = ax.legend(loc='upper right', borderaxespad=0.5)

            if legendYoffset != 0.0:
                # Get the bounding box of the original legend
                bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)

                # Change to location of the legend.
                bb.y0 += legendYoffset
                bb.y1 += legendYoffset
                leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

            if legendXoffset != 0.0:
                # Get the bounding box of the original legend
                bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)

                # Change to location of the legend.
                bb.x0 += legendXoffset
                bb.x1 += legendXoffset
                leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

        subplot_adjust = subplot_adjust or {
            'bottom': 0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
            dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return

    def plot_2d_infections_at_time(self, sim, at_time, density_bandwidth=1.0, restart=0,
        title='Example', filename='2d_inf_0', figsize=(10, 10), acc=1000, ymax=None):

        '''
        Plots 2d visualization using mobility object. The bandwidth set by `density_bandwidth`
        determines the bandwidth of the RBF kernel in KDE used to generate the plot.
        Smaller means more affected by local changes. Set the colors and markers in the __init__ function
        '''
        if acc > sim.max_time:
            acc = int(sim.max_time)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        # infections
        r = restart
        is_expo = is_state_at(sim, r, 'expo', at_time)
        is_iasy = is_state_at(sim, r, 'iasy', at_time)
        is_ipre = is_state_at(sim, r, 'ipre', at_time)
        is_isym = is_state_at(sim, r, 'isym', at_time)
        is_infected = is_iasy | is_ipre | is_isym
        no_state = (1 - is_infected) & (1 - is_expo)

        idx_expo = np.where(is_expo)[0]
        idx_infected = np.where(is_infected)[0]
        idx_none = np.where(no_state)[0]

        # self.color_isym = 'red'
        # self.color_expo= 'yellow'


        ### sites
        site_loc = sim.site_loc
        ax.scatter(site_loc[:, 0], site_loc[:, 1], alpha=self.filling_alpha, label='public sites',
                   marker=self.marker_site, color=self.color_site, facecolors=self.color_site, s=self.size_site)


        ### home locations and their states
        home_loc = sim.home_loc
        # no state
        ax.scatter(home_loc[idx_none, 0], home_loc[idx_none, 1],
                   marker=self.marker_home, color=self.color_home,
                   facecolors='none', s=self.size_home)

        try:
            # expo
            ax.scatter(home_loc[idx_expo, 0], home_loc[idx_expo, 1],
                    marker=self.marker_home, color=self.color_home,
                    facecolors=self.color_expo, s=self.size_home, label='exposed households')
            sns.kdeplot(home_loc[idx_expo, 0], home_loc[idx_expo, 1], shade=True, alpha=self.density_alpha,
                        shade_lowest=False, cbar=False, ax=ax, color=self.color_expo, bw=density_bandwidth, zorder=0)

            # infected
            ax.scatter(home_loc[idx_infected, 0], home_loc[idx_infected, 1],
                    marker=self.marker_home, color=self.color_home,
                    facecolors=self.color_isym, s=self.size_home, label='infected households')
            sns.kdeplot(home_loc[idx_infected, 0], home_loc[idx_infected, 1], shade=True, alpha=self.density_alpha,
                        shade_lowest=False, cbar=False, ax=ax, color=self.color_isym, bw=density_bandwidth, zorder=0)

        except:
            print('KDE failed, likely no exposed and infected at this time. Try different timing.')
            plt.close()
            return

        # axis
        ax.set_xlim((-0.1, 1.1))
        ax.set_ylim((-0.1, 1.1))
        plt.axis('off')

        # legend
        fig.legend(loc='center right', borderaxespad=0.1)
        # Adjust the scaling factor to fit your legend text completely outside the plot
        plt.subplots_adjust(right=0.85)

        ax.set_title(title, pad=20)
        plt.draw()
        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI, bbox_inches='tight')
        if NO_PLOT:
            plt.close()
        return

    def compare_hospitalizations_over_time(self, sims, titles, figtitle='Hospitalizations', filename='compare_hosp_0',
        capacity_line_at=20, figsize=(10, 10), errorevery=20, acc=500, ymax=None):
        ''''
        Plots total hospitalizations for each simulation, named as provided by `titles`
        to compare different measures/interventions taken. Colors taken as defined in __init__, and
        averaged over random restarts, using error bars for std-dev.
        The value of `capacity_line_at` defines the y-intercept of the hospitalization capacity line
        '''
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        for i in range(len(sims)):
            if acc > sims[i].max_time:
                acc = int(sims[i].max_time)

            ts, line_hosp, error_sig = comp_state_over_time(
                sims[i], 'hosp', acc)
            line_xaxis = np.zeros(ts.shape)

            # lines
            ax.errorbar(ts, line_hosp, yerr=error_sig, errorevery=errorevery,
                        c='black', linestyle='-', elinewidth=0.8)

            # filling
            ax.fill_between(ts, line_xaxis, line_hosp, alpha=self.filling_alpha, zorder=0,
                            label=r'Hospitalized under: ' + titles[i], edgecolor=self.color_different_scenarios[i],
                            facecolor=self.color_different_scenarios[i], linewidth=0)

        # capacity line
        ax.plot(ts, capacity_line_at * np.ones(ts.shape[0]), label=r'Max. hospitalization capacity',
                    c='red', linestyle='--', linewidth=4.0)

        # axis
        ax.set_xlim((0, np.max(ts)))
        if ymax is None:
            ymax = 1.5 * np.max(line_hosp + error_sig)
        ax.set_ylim((0, ymax))

        ax.set_xlabel(r'$t$ [days]')
        ax.set_ylabel(r'[people]')

        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

        # legend
        fig.legend(loc='center right', borderaxespad=0.1)
        # Adjust the scaling factor to fit your legend text completely outside the plot
        plt.subplots_adjust(right=0.70)
        ax.set_title(figtitle, pad=20)
        plt.draw()
        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI, bbox_inches='tight')
        if NO_PLOT:
            plt.close()
        return

    def plot_positives_vs_target(self, sims, titles, targets, title='Example',
        filename='inference_0', figsize=None, figformat='triple', errorevery=1, acc=17, ymax=None,
        start_date='1970-01-01', lockdown_label='Lockdown', lockdown_at=None,
        lockdown_label_y=None, subplot_adjust=None, n_age_groups=None, small_figure=False, show_legend=True):
        ''''
        Plots daily tested averaged over random restarts, using error bars for std-dev
        together with targets from inference
        '''
        # Set triple figure format
        self._set_matplotlib_params(format=figformat)

        fig, ax = plt.subplots(figsize=figsize)

        for i, sim in enumerate(sims):
            if isinstance(sim, str):
                try:
                    data = load_condensed_summary(sim, acc)
                except FileNotFoundError:
                    acc = create_condensed_summary_from_path(sim, acc=acc, n_age_groups=n_age_groups)
                    data = load_condensed_summary(sim, acc=acc)
                acc = data['acc']
                ts = data['ts']
                posi_mu = data['posi_mu']
                posi_sig = data['posi_sig']
            else:
                if acc > sim.max_time:
                    acc = int(sim.max_time)
                ts, posi_mu, posi_sig = comp_state_over_time(sim, 'posi', acc)
            plain_ts = ts
            # Convert x-axis into posix timestamps and use pandas to plot as dates
            ts = days_to_datetime(ts, start_date=start_date)
            # lines
            ax.plot(ts, posi_mu, label=titles[i], c=self.color_different_scenarios[i])
            ax.fill_between(ts, posi_mu - 2 * posi_sig, posi_mu + 2 * posi_sig,
                            color=self.color_different_scenarios[i],
                            alpha=self.filling_alpha, linewidth=0.0)
        # target
        if small_figure:
            target_widget(targets, start_date, ax, label='Real cases', ms=1.0)
        else:
            target_widget(targets, start_date, ax, label='Real cases')
        if ymax is None:
            ymax = 1.5 * np.max(posi_mu)
        ax.set_ylim((0, ymax))
        ax.set_ylabel(r'Positive cases')
        # lockdown
        if lockdown_at is not None:
            if small_figure:
                xshift = 3.5 * pd.to_timedelta(pd.to_datetime(ts[-1]) - pd.to_datetime(start_date), 'd') / 54
                text_off = True
            else:
                xshift = 2.5 * pd.to_timedelta(pd.to_datetime(ts[-1]) - pd.to_datetime(start_date), 'd') / 54
                text_off = True
            lockdown_widget(ax, lockdown_at, start_date,
                            lockdown_label_y,
                            lockdown_label, xshift=xshift, text_off=text_off)
        # Default axes style
        self._set_default_axis_settings(ax=ax)
        # y-ticks
        if small_figure:
            if ymax > 700:
                ax.yaxis.set_major_locator(ticker.MultipleLocator(500))
            else:
                ax.yaxis.set_major_locator(ticker.MultipleLocator(250))
        # x-ticks
        if small_figure:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=2, interval=4))
        else:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        #set major ticks format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        # legend
        if show_legend:
            if small_figure:
                ax.legend(loc='upper left',
                          bbox_to_anchor=(0.025, 0.99),
                          bbox_transform=ax.transAxes,)
            else:
                ax.legend(loc='upper left', borderaxespad=0.5)
        # Save fig
        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')
        if NO_PLOT:
            plt.close()
        return plain_ts, posi_mu

    def plot_age_group_positives_vs_target(self, sim, targets, ytitle=None,
                                 filename='inference_0', figsize=(6, 5), errorevery=1, acc=17, ymax=None,
                                 start_date='1970-01-01', lockdown_label='Lockdown', lockdown_at=None,
                                 lockdown_label_y=None, subplot_adjust=None):

        ''''
        Plots daily tested averaged over random restarts, using error bars for std-dev
        together with targets from inference
        '''

        n_age_groups = targets.shape[1]
        if n_age_groups == 6:
            age_groups = ['0-4', '5-15', '15-34', '35-59', '60-79', '80+']
        else:
            age_groups = ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']

        if isinstance(sim, str):
            try:
                data = load_condensed_summary(sim, acc=acc)
            except FileNotFoundError:
                acc = create_condensed_summary_from_path(sim, acc=acc, n_age_groups=n_age_groups)
                data = load_condensed_summary(sim, acc=acc)
        else:
            if acc > sim.max_time:
                acc = int(sim.max_time)

        fig, axs = plt.subplots(1, n_age_groups, figsize=figsize)

        for i, age in enumerate(range(n_age_groups)):

            if isinstance(sim, str):
                ts = data['ts']
                posi_mu = data['posi_mu_age'][i]
                posi_sig = data['posi_sig_age'][i]
            else:
                # automatically shifted by `test_lag` in the function
                ts, posi_mu, posi_sig = comp_state_over_time_per_age(sim, 'posi', acc, age)

            T = posi_mu.shape[0]

            xx = days_to_datetime(ts, start_date=start_date)
            axs[age].plot(xx, posi_mu, c=self.color_different_scenarios[0], linestyle='-',
                    label='COVID-19 simulated case data')
            axs[age].fill_between(xx, posi_mu - 2 * posi_sig, posi_mu + 2 * posi_sig,
                            color=self.color_different_scenarios[0], alpha=0.1, linewidth=0.0)

            # target
            target_widget(targets[:, age], start_date, axs[age], ms=4)

            # axis
            #ax.set_xlim((0, np.max(ts)))
            if ymax is None:
                ymax = 1.5 * np.max(posi_mu)
            axs[age].set_ylim((0, ymax))

            # ax.set_xlabel('Days')
            if age == 0:
                if ytitle is not None:
                    axs[age].set_ylabel(ytitle)

            axs[age].set_title(f'{age_groups[age]} years')

            if lockdown_at is not None:
                xshift = 2.5 * pd.to_timedelta(pd.to_datetime(ts[-1]) - pd.to_datetime(start_date), 'd') / 54
                lockdown_widget(axs[age], lockdown_at, start_date,
                                lockdown_label_y,
                                lockdown_label, xshift=xshift)

            # Hide the right and top spines
            axs[age].spines['right'].set_visible(False)
            axs[age].spines['top'].set_visible(False)
            axs[age].spines['left'].set_visible(False)
            axs[age].spines['bottom'].set_visible(False)
            axs[age].get_xaxis().set_ticks([])

            axs[age].set_xlabel(r'$t$')
            # axs[age].set_ylabel(r'Cases')

            # Only show ticks on the left and bottom spines
            # axs[age].yaxis.set_ticks_position('left')

            #set ticks every week
            # axs[age].xaxis.set_major_locator(mdates.WeekdayLocator())
            #set major ticks format
            # axs[age].xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            # fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')

        # legend
        # axs[age].legend(loc='upper left', borderaxespad=0.5)

        subplot_adjust = subplot_adjust or {
            'bottom': 0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)
        plt.tight_layout()
        plt.draw()

        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI)  # , bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return

    def plot_daily_rts(self, sims, filename, start_date='1970-01-01', x_axis_dates=True, titles=None, sigma=None,
                       r_t_range=R_T_RANGE, window=3, figsize=(6, 5),
                       subplot_adjust=None, lockdown_label='Lockdown',
                       lockdown_at=None, lockdown_label_y=None, ymax=None,
                       colors=['grey'], fill_between=True, draw_dots=True,
                       errorevery=1, show_legend=False, xtick_interval=2, ci=0.9):

        # If a single summary is provided
        if not isinstance(sims, list):
            sims = [sims]
            sigma = [sigma]

        results = list()
        for i, sim in enumerate([sims[0]]):
            res = compute_daily_rts(sim, start_date, sigma[i], r_t_range, window, ci)
            results.append(res)

        # Colors
        ABOVE = [1,0,0]
        MIDDLE = [1,1,1]
        BELOW = [0,0,0]
        cmap = ListedColormap(np.r_[
            np.linspace(BELOW,MIDDLE,25),
            np.linspace(MIDDLE,ABOVE,25)
        ])
        color_mapped = lambda y: np.clip(y, .5, 1.5)-.5

        ymax_computed = 0.0  # Keep track of max y to set limit

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        for i, result in enumerate(results):
            if x_axis_dates:
                index = result['ML'].index
            else:
                index = np.arange(0, len(result['ML'].index))
            values = result['ML'].values

            # Plot dots and line
            ax.plot(index, values, c=colors[i], zorder=1, alpha=1.0)

            if draw_dots:
                ax.scatter(index, values, s=40, lw=0.0,
                           c=cmap(color_mapped(values)),
                           edgecolors='k', zorder=2)

            # Aesthetically, extrapolate credible interval by 1 day either side
            if x_axis_dates:
                lowfn = interp1d(date2num(index), result[f'Low_{ci*100:.0f}'].values,
                                bounds_error=False, fill_value='extrapolate')
                highfn = interp1d(date2num(index), result[f'High_{ci*100:.0f}'].values,
                                bounds_error=False, fill_value='extrapolate')

                extended = pd.date_range(start=index[0], end=index[-1])
                error_low = lowfn(date2num(extended))
                error_high = highfn(date2num(extended))
            else:
                lowfn = interp1d(index, result[f'Low_{ci * 100:.0f}'].values,
                                 bounds_error=False, fill_value='extrapolate')
                highfn = interp1d(index, result[f'High_{ci * 100:.0f}'].values,
                                  bounds_error=False, fill_value='extrapolate')

                extended = index
                error_low = lowfn(extended)
                error_high = highfn(extended)

            if fill_between:
                ax.fill_between(extended, error_low, error_high,
                                color=colors[i], alpha=0.1, linewidth=0.0)
            else:
                # Ignore first value which is just prior, not informed by data
                ax.errorbar(x=index[1:], y=values[1:], label=titles[i],
                            yerr=np.vstack((result[f'Low_{ci*100:.0f}'], result[f'High_{ci*100:.0f}']))[:,1:],
                            color=colors[i], linewidth=1.0,
                            elinewidth=0.8, capsize=3.0,
                            errorevery=errorevery)

            ymax_computed = max(ymax_computed, np.max(error_high))

            # Plot horizontal line at R_t = 1
            ax.axhline(1.0, c='k', lw=1, alpha=.25);

        # limits
        ymax = ymax or 1.2 * ymax_computed
        ax.set_ylim((0, ymax_computed))

        if show_legend:
            ax.legend(loc='upper left', borderaxespad=0.5)

        # extra
        if lockdown_at is not None:
            xshift = 2.5 * pd.to_timedelta(pd.to_datetime(index[-1]) - pd.to_datetime(start_date), 'd') / 54
            lockdown_widget(ax, lockdown_at, start_date,
                            lockdown_label_y,
                            lockdown_label, zorder=-200, xshift=xshift)

        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')

        # Set label
        ax.set_ylabel(r'$R_t$')
        if x_axis_dates:
            #set ticks every week
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=xtick_interval))
            #set major ticks format
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        else:
            ax.set_xlabel(r'$t$ [days]')

        subplot_adjust = subplot_adjust or {'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.savefig('plots/' + filename + '.png', format='png', facecolor=None,
                    dpi=DPI)#, bbox_inches='tight')

        if NO_PLOT:
            plt.close()

    def plot_daily_nbinom_rts(self, path, filename='daily_nbinom_rts_0',
                              slider_size=24.0, window_size=24.*7, end_cutoff=24.*10,
                              figsize=None, figformat='double', ymax=None, acc=500,
                              cmap_range=(0.5, 1.5), subplots_adjust={'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96},
                              lockdown_label='Lockdown', lockdown_at=None, lockdown_label_y=None, lockdown_xshift=0.0,
                              x_axis_dates=True, xtick_interval=2, xlim=None):
        # Set this plot with double figures parameters
        self._set_matplotlib_params(format=figformat)

        # Compute statistics
        try:
            data = load_condensed_summary(path, acc)
        except FileNotFoundError:
            acc = create_condensed_summary_from_path(sim, acc=acc)
            data = load_condensed_summary(sim, acc)

        df = data['nbinom_rts']
            
        # Format dates
        if x_axis_dates:
            # Cast time of end of interval to datetime
            df['date_end'] = days_to_datetime(
                df['t1'] / 24, start_date=result.metadata.start_date)
            # Aggregate results by date
            df_agg = df.groupby('date_end').agg({'Rt': ['mean', 'std'],
                                                'kt': ['mean', 'std']})
        else:
            df['time'] = df['t1'] / 24
            df_agg = df.groupby('time').agg({'Rt': ['mean', 'std'],
                                             'kt': ['mean', 'std']})
        # Build dot colormap: black to white to red
        ABOVE = [1,0,0]
        MIDDLE = [1,1,1]
        BELOW = [0,0,0]
        cmap_raw = ListedColormap(np.r_[
            np.linspace(BELOW,MIDDLE,25),
            np.linspace(MIDDLE,ABOVE,25)
        ])
        def cmap_clipped(y):
            vmin, vmax = cmap_range
            return cmap_raw((np.clip(y, vmin, vmax) - vmin) / (vmax - vmin))
        # Plot figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        y_m = df_agg.Rt['mean']
        y_std = df_agg.Rt['std']
        # Plot estimated mean values (fill +/- std) with colored dots
        plt.fill_between(df_agg.index, y_m - y_std, y_m + y_std,
                        color='lightgray', linewidth=0.0, alpha=0.5)
        plt.plot(df_agg.index, y_m, c='grey')
        plt.scatter(df_agg.index, y_m, s=4.0, lw=0.0, c=cmap_clipped(y_m),
                    edgecolors='k', zorder=100)
        # Horizotal line at R_t = 1.0
        plt.axhline(1.0, c='lightgray', zorder=-100)
        # extra
        if lockdown_at is not None:
            xshift = (2.5 * pd.to_timedelta(pd.to_datetime(df_agg.index[-1])
                      - pd.to_datetime(result.metadata.start_date), 'd') / 54)
            ax.axvline(pd.to_datetime(lockdown_at), c='black', ls='--',
                       label='_nolegend_', zorder=-200)
            ax.text(x=lockdown_at + pd.Timedelta(lockdown_xshift, unit='d'),
                    y=lockdown_label_y, s=lockdown_label,
                    rotation=90, #fontdict={'fontsize': 5.5}
                    )

        if x_axis_dates:
            # set xticks every week
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=1, interval=1))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=1, interval=xtick_interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            fig.autofmt_xdate(bottom=0.2, rotation=0, ha='center')
        else:
            ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
            ax.set_xlabel(r'$t$ [days]')
        # set yticks to units
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        # Set labels
        ax.set_ylabel(r'$R_t$')
        # Set limits
        ax.set_ylim(bottom=0.0, top=ymax)
        if xlim:
            ax.set_xlim(*xlim)
        # Set default axes style
        self._set_default_axis_settings(ax=ax)
        plt.subplots_adjust(**subplots_adjust)
        # Save plot
        fpath = f"plots/daily-nbinom-rts-{filename}.pdf"
        plt.savefig(fpath, format='pdf')
        print("Save:", fpath)
        if NO_PLOT:
            plt.close()

    def plot_nbinom_distributions(self, *, path, acc=500, figsize=FIG_SIZE_TRIPLE_TALL, figformat='triple',
                                  label_range=[], ymax=None, filename='nbinom_dist_0'):
        """
        Plot the distribution of number of secondary cases along with their Negative-Binomial fits
        for the experiment summary in `result` for several ranges of times.
        A pre-computed dataframe `df` can also be provided
        """

        # Compute statistics
        try:
            data = load_condensed_summary(path, acc)
        except FileNotFoundError:
            acc = create_condensed_summary_from_path(sim, acc=acc)
            data = load_condensed_summary(sim, acc)

        x_range = np.arange(0, 20)
        t0_range = [50 * 24.0]
        window_size = 10.0 * 24
        interval_range = [(t0, t0 + window_size) for t0 in t0_range]
        df = data['nbinom_dist']
            
        # Aggregate results by time
        df_agg = df.groupby('t0').agg({'nbinom_pmf': list,
                                    'Rt': ['mean', 'std'],
                                    'kt': ['mean', 'std']})
        # Set triple figure params
        self._set_matplotlib_params(format=figformat)
        # Draw figures
        for i, (t0, label) in enumerate(zip(t0_range, label_range)):
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            # Extract data for the plot
            row_df = df.loc[df.t0 == t0]
            row_df_agg = df_agg.loc[t0]
            y_nbinom = np.nanmean(np.vstack(row_df_agg['nbinom_pmf']), axis=0)
            # Plot histogram
            plt.hist(np.hstack(row_df['num_sec_cases']),
                    bins=x_range, density=True,
                    color='darkgray',
                    align='left', width=0.8,
                    label='Empirical')
            # Plot NB pmf
            plt.plot(x_range, y_nbinom,
                    color='k',
                    label='NB')
            # Write estimates in text
            text_x = 0.999
            text_y = 0.28
            plt.text(text_x, text_y + 0.15, transform=ax.transAxes, horizontalalignment='right',
                    s=r'$R_t ~=~' + f"{row_df_agg['Rt']['mean']:.2f} \pm ({row_df_agg['Rt']['std']:.2f})$")
            plt.text(text_x, text_y, transform=ax.transAxes, horizontalalignment='right',
                    s=r'$k_t ~=~' + f"{row_df_agg['kt']['mean']:.2f} \pm ({row_df_agg['kt']['std']:.2f})$")
            # Set layout and labels
            plt.ylim(top=ymax)
            ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
            plt.xlabel('Number of Secondary Cases')
            plt.ylabel('Probability')
            plt.legend(loc='upper right')
            # Set default axis style
            self._set_default_axis_settings(ax=ax)
            plt.subplots_adjust(left=0.22, bottom=0.22, right=0.99, top=0.95)
            # Save figure
            fpath = f"plots/prob-secondaryCases-{filename}-{i}-{label}.pdf"
            print('Save:', fpath)
            plt.savefig(fpath)
            os.system(f'pdfcrop "${fpath}" tmp.pdf && mv tmp.pdf "${fpath}"')
            plt.close()

    def plot_roc_curve(self, titles, summaries=None, paths=None, action='isolate', figformat='double',
                       filename='roc_example', figsize=None):
        ''''
        ROC curve
        '''
        assert (summaries or paths) is not None and (summaries and paths) is None, "Specify either summaries or paths"
        self._set_matplotlib_params(format=figformat)
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        axs = [ax]
        # fig, axs = plt.subplots(1, 2, figsize=figsize)

        # xs
        xs = np.linspace(0, 1, num=500)

        if paths:
            try:
                summaries = [load_condensed_summary(path) for path in paths]
            except FileNotFoundError:
                for path in paths:
                    _ = create_condensed_summary_from_path(path)
                summaries = [load_condensed_summary(path) for path in paths]

        for i, summary in enumerate(summaries):

            if paths: # If condensed summary
                tracing_stats = summary['tracing_stats']
            else:
                print('exposed:', np.sum(summary.state_started_at['expo'] < np.inf, axis=1).mean())
                tracing_stats = summary.tracing_stats
            thresholds = list(tracing_stats.keys())

            policies = dict()

            for j, (name, policy) in enumerate([('PanCast', 'sites'), ('SPECT', 'no_sites')]):

                
                fpr_mean, fpr_std = [], []
                tpr_mean, tpr_std = [], []

                precision_mean, precision_std = [], []
                recall_mean, recall_std = [], []
                
                fpr_of_means = []
                tpr_of_means = []     
                precision_of_means = []
                recall_of_means = []

                fpr_single_runs = [[] for _ in range(len(tracing_stats[thresholds[0]][policy]['isolate']['tn']))]     
                tpr_single_runs = [[] for _ in range(len(tracing_stats[thresholds[0]][policy]['isolate']['tn']))]   


                for t, thres in enumerate(thresholds):

                    stats = tracing_stats[thres][policy][action]


                    # FPR = FP/(FP + TN) [isolate + not infected / not infected]
                    # [if FP = 0 and TN = 0, set to 0]
                    fprs = stats['fp'] / (stats['fp'] + stats['tn'])
                    fprs = np.nan_to_num(fprs, nan=0.0)
                    fpr_mean.append(np.mean(fprs).item())
                    fpr_std.append(np.std(fprs).item())
                    fpr_of_means.append(stats['fp'].mean() / (stats['fp'].mean() + stats['tn'].mean()))

                    for r in range(len(fpr_single_runs)):
                        fpr_single_runs[r].append(fprs[r])

                    # TPR = TP/(TP + FN) [isolate + infected / infected]
                    # = RECALL
                    # [if TP = 0 and FN = 0, set to 0]
                    tprs = stats['tp'] / (stats['tp'] + stats['fn'])
                    tprs = np.nan_to_num(tprs, nan=0.0)
                    tpr_mean.append(np.mean(tprs).item())
                    tpr_std.append(np.std(tprs).item())
                    tpr_of_means.append(stats['tp'].mean() / (stats['tp'].mean() + stats['fn'].mean()))

                    for r in range(len(tpr_single_runs)):
                        tpr_single_runs[r].append(tprs[r])

                    # precision = TP/(TP + FP)
                    precs = stats['tp'] / (stats['tp'] + stats['fp'])
                    precs = np.nan_to_num(precs, nan=0.0)
                    precision_mean.append(np.mean(precs).item())
                    precision_std.append(np.std(precs).item())
                    precision_of_means.append(stats['tp'].mean() / (stats['tp'].mean() + stats['fp'].mean()))

                    # if i == 0:
                    print("{:1.3f}   TP {:5.2f} FP {:5.2f}  TN {:5.2f}  FN {:5.2f}".format(
                        thres, stats['tp'].mean(), stats['fp'].mean(), stats['tn'].mean(), stats['fn'].mean()
                    ))
                    if t == len(thresholds) - 1:
                        print(" P {:5.2f}  N {:5.2f}".format(
                            (stats['fn'] + stats['tp']).mean(), (stats['fp'] + stats['tn']).mean()
                        ))

                policies[name] = {'fpr': fpr_of_means,
                                  'tpr': tpr_of_means, 
                                  'prec': precision_of_means}

                # lines
                axs[0].plot(fpr_of_means, tpr_of_means, linestyle='-', label=name, c=self.color_different_scenarios[j])
                # axs[1].plot(tpr_of_means, precision_of_means, linestyle='-', label=name, c=self.color_different_scenarios[j])

                # axs[0].plot(fpr_mean, tpr_mean, linestyle='-', label=name, c=self.color_different_scenarios[j])
                # axs[1].plot(tpr_mean, precision_mean, linestyle='-', label=name, c=self.color_different_scenarios[j])

            # for each FPR bucket, collect TPR and prec values
            policy_bin_values = dict()
            n_bins = 6
            bins = np.linspace(0.0, 1.0, n_bins)
            for n in range(bins.shape[0] - 1):
                print(f'index {n + 1} : {bins[n]} - {bins[n + 1]}')

            for policy in ['SPECT', 'PanCast']:
                fprs = np.array(policies[policy]['fpr'])
                tprs = np.array(policies[policy]['tpr'])
                precs = np.array(policies[policy]['prec'])

                inds = np.digitize(fprs, bins)

                bin_values_fpr = collections.defaultdict(list)
                bin_values_tpr = collections.defaultdict(list)
                bin_values_prec = collections.defaultdict(list)

                for i in range(fprs.shape[0]):
                    bin_values_fpr[inds[i]].append(fprs[i])
                    bin_values_tpr[inds[i]].append(tprs[i])
                    bin_values_prec[inds[i]].append(precs[i])

                # form mean of each bucket
                policy_bin_values[policy] = {
                    'fpr' : {k:np.array(lst).mean().item() for k, lst in bin_values_fpr.items()},
                    'tpr' : {k:np.array(lst).mean().item() for k, lst in bin_values_tpr.items()},
                    'prec': {k: np.array(lst).mean().item() for k, lst in bin_values_prec.items()},
                }

            # print improvement pancast over spect
            # pprint.pprint(policy_bin_values)
            for metric in ['tpr', 'prec']:

                relative_percentage = []
                
                for ind in policy_bin_values['SPECT']['fpr'].keys():

                    # only check bins where both have values
                    if (ind not in policy_bin_values['PanCast'][metric].keys()) or\
                       (ind not in policy_bin_values['SPECT'][metric].keys()):
                       continue

                    # ignore edge bins
                    if ind <= 1 or ind >= n_bins - 1:
                        continue 

                    relative_percentage.append(
                        (ind, policy_bin_values['PanCast'][metric][ind] / policy_bin_values['SPECT'][metric][ind])
                    )

                argmaxval, maxval = max(relative_percentage, key=lambda x: x[1])
                print('Maximum relative % PanCast/SPECT (excluding boundary)', metric, maxval * 100, 'bin: ', argmaxval)

        for ax in axs:
            ax.set_xlim((0.0, 1.0))
            ax.set_ylim((0.0, 1.0))

        # diagonal
        axs[0].plot(xs, xs, linestyle='dotted', c='black')

        axs[0].set_xlabel('FPR')
        axs[0].set_ylabel('TPR')

        # axs[1].set_xlabel('Recall')
        # axs[1].set_ylabel('Precision')

        # Set default axes style
        # self._set_default_axis_settings(ax=ax)
        
        leg = axs[0].legend(loc='lower right')
        # leg = axs[1].legend(loc='top right')

        # subplot_adjust = subplot_adjust or {'bottom':0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        # plt.subplots_adjust(**subplot_adjust)

        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')
        plt.tight_layout()
        if NO_PLOT:
            plt.close()
        return

    def reff_heatmap(self, xlabel, ylabel, paths, path_labels, figformat='double',
                     filename='reff_heatmap_0', figsize=None, acc=500, 
                     relative_window=(0.25, 0.75)):
        ''''
        Plots heatmap of average R_t
            paths:              list with tuples (x, y, path)
            relative_window:    relative range of max_time used for R_t average
        '''
        # set double figure format
        self._set_matplotlib_params(format=figformat)

        # draw figure
        fig, axs = plt.subplots(1, 2, figsize=figsize)

        # extract data
        reff_means_all = []
        for p in paths:

            reff_means = []
            for xval, yval, path in p:

                try:
                    data = load_condensed_summary(path, acc)
                except FileNotFoundError:
                    acc = create_condensed_summary_from_path(sim, acc=acc)
                    data = load_condensed_summary(sim, acc)

                rtdata = data['nbinom_rts']
                n_rollouts = data['metadata'].random_repeats
                max_time = data['max_time']

                l_max_time = relative_window[0] * max_time 
                r_max_time = relative_window[1] * max_time

                # filter time window
                rtdata_window = rtdata.loc[(l_max_time <= rtdata['t0']) & (rtdata['t1'] <= r_max_time)]
                reff_mean = np.mean(rtdata_window["Rt"])
        
                reff_means.append((xval, yval, reff_mean))

            reff_means_all.append(reff_means)

        # find min and max for both plots
        zmins, zmaxs = [], []
        for reff_means in reff_means_all:
            x, y, z = zip(*reff_means)
            zmins.append(min(z))
            zmaxs.append(max(z))

        zmin, zmax = min(zmins), max(zmaxs)

        # generate heatmaps
        for t, title in enumerate(path_labels):
            
            x, y, z = zip(*reff_means_all[t])
            xbounds = min(x), max(x)
            ybounds = min(y), max(y)

            # contour interpolation
            xi = np.linspace(xbounds[0], xbounds[1], 100)
            yi = np.linspace(ybounds[0], ybounds[1], 100)
            zi = griddata((x, y), z, (xi[None,:], yi[:,None]), method='cubic')

            n_bins = 15
            axs[t].contour(xi, yi, zi, n_bins, linewidths=0.5, colors='k', norm=colors.Normalize(vmin=zmin, vmax=zmax))

            if t == 0:
                contourplot = axs[t].contourf(xi, yi, zi, n_bins, cmap=plt.cm.jet, norm=colors.Normalize(vmin=zmin, vmax=zmax))
            else:
                _ = axs[t].contourf(xi, yi, zi, n_bins, cmap=plt.cm.jet, norm=colors.Normalize(vmin=zmin, vmax=zmax))

            axs[t].set_xlabel(xlabel)
            if t == 0:
                axs[t].set_ylabel(ylabel)
            axs[t].set_xlim(xbounds)
            axs[t].set_ylim(ybounds)
            axs[t].set_title(title)

        fig.subplots_adjust(right=0.8)
        cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
        fig.colorbar(contourplot, cax=cbar_ax)


        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return
    
    def relative_quantity_heatmap(self, mode, xlabel, ylabel, paths, path_labels, baseline_path, figformat='double',
                     filename='reff_heatmap_0', figsize=None, acc=500, interpolate='linear', # or `cubic`
                     width_ratio=4, cmap='jet'):
        ''''
        Plots heatmap of average R_t
            paths:              list with tuples (x, y, path)
            relative_window:    relative range of max_time used for R_t average
        '''
        if mode == 'cumu_infected':
            key = 'cumu_infected_'
            colorbar_label = r'\% reduction of infections'
        elif mode == 'hosp':
            key = 'hosp_'
            colorbar_label = r'\% reduction of peak hosp.'
        elif mode == 'dead':
            key = 'cumu_dead_'
            colorbar_label = r'\% reduction of deaths'

        # set double figure format
        self._set_matplotlib_params(format=figformat)

        # draw figure
        fig, axs = plt.subplots(1, 2, figsize=figsize,  gridspec_kw={'width_ratios': [1, width_ratio]})

        baseline_data = load_condensed_summary(baseline_path)
        baseline_series = baseline_data[key + 'mu']

        # extract data
        zval_means_all = []
        for p in paths:

            zval_means = []
            for xval, yval, path in p:

                try:
                    data = load_condensed_summary(path, acc)
                except FileNotFoundError:
                    acc = create_condensed_summary_from_path(sim, acc=acc)
                    data = load_condensed_summary(sim, acc)

                # extract z value given (x, y)
                series = data[key + 'mu']
                if 'cumu' in key:
                    # last
                    zval = (1 - series[-1] / baseline_series[-1]) * 100
                else:
                    # peak
                    zval = (1 - series.max() / baseline_series.max()) * 100
        
                zval_means.append(((xval * 100 if xval is not None else xval), yval * 100, zval.item()))

            zval_means_all.append(zval_means)

        # define min and max for both plots
        zmin, zmax_color, zmax_colorbar = 0, 90, 90
        stepsize = 5
        norm = colors.Normalize(vmin=zmin, vmax=zmax_color)
        levels = np.arange(zmin, zmax_colorbar + stepsize, stepsize)

        # generate heatmaps
        for t, title in enumerate(path_labels):
            
            x, y, z = zip(*zval_means_all[t])

            if x[0] is None:
                # move 1D data on a 2D manifold for plotting
                xbounds = (-0.1, 0.1)
                ybounds = min(y), max(y)   

                x = [xbounds[0] for _ in y] + [xbounds[1] for _ in y]
                y = y + y
                z = z + z

                axs[t].xaxis.set_major_formatter(plt.NullFormatter())
                axs[t].xaxis.set_minor_formatter(plt.NullFormatter())
                axs[t].xaxis.set_major_locator(plt.NullLocator())
                axs[t].xaxis.set_minor_locator(plt.NullLocator())
                
            else:
                x = np.log(x)
                xbounds = min(x), max(x)
                ybounds = min(y), max(y)        

                axs[t].set_xlabel(xlabel)

                # x ticks
                @ticker.FuncFormatter
                def major_formatter(x_, pos):
                    return r"{:3.0f}".format(np.exp(x_))
        
                # for some reason, FixedLocator makes tick labels falsely bold
                # axs[t].xaxis.set_major_locator(ticker.FixedLocator(x)) 
                axs[t].xaxis.set_major_locator(CustomSitesProportionFixedLocator())
                axs[t].xaxis.set_major_formatter(major_formatter)
                                        
            # contour interpolation
            xi = np.linspace(xbounds[0], xbounds[1], 100)
            yi = np.linspace(ybounds[0], ybounds[1], 100)
            zi = griddata((x, y), z, (xi[None,:], yi[:,None]), method=interpolate)

            # contour plot
            axs[t].contour(xi, yi, zi, linewidths=0.5, colors='k', norm=norm, levels=levels)
            contourplot = axs[t].contourf(xi, yi, zi, cmap=cmap, norm=norm, levels=levels)

            # axis
            axs[t].set_xlim(xbounds)
            axs[t].set_ylim(ybounds)
            axs[t].set_title(title)

            if t == 0:
                axs[t].set_ylabel(ylabel)
            else:
                pass

        # layout and color bar
        fig.tight_layout()
        fig.subplots_adjust(right=0.8)

        # [left, bottom, width, height]
        cbar_ax = fig.add_axes([0.87, 0.17, 0.05, 0.7])
        cbar = matplotlib.colorbar.ColorbarBase(
            cbar_ax, cmap=plt.cm.RdYlGn,
            norm=norm,
            boundaries=levels,
            ticks=levels[::2],
            orientation='vertical')
        cbar.set_label(colorbar_label, labelpad=5.0)

        # save
        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return


    def compare_peak_reduction(self, path_dict, baseline_path, ps_adoption, titles,
                               mode='cumu_infected', ymax=1.0,
                               figformat='double', filename='cumulative_reduction', figsize=None,
                               show_legend=True, legend_is_left=False, subplot_adjust=None):

        if mode == 'cumu_infected':
            key = 'cumu_infected_'
            ylabel = 'Reduction in infections'
        elif mode == 'hosp':
            key = 'hosp_'
            ylabel = 'Reduction in peak hospitalizations'
        elif mode == 'dead':
            key = 'cumu_dead_'
            ylabel = 'Reduction in fatalities'

        # Set double figure format
        self._set_matplotlib_params(format=figformat)
        # Draw figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        baseline_data = load_condensed_summary(baseline_path)
        baseline_norm = np.max(baseline_data[key+'mu'])

        ps_adoption = ps_adoption + [0]

        for i, paths in enumerate(path_dict.values()):
            cumu_rel_mean = []
            cumu_rel_std = []
            for path in paths:
                data = load_condensed_summary(path)
                maxidx = np.argmax(data[key + 'mu'])
                cumu_rel_mean.append(data[key+'mu'][maxidx] / baseline_norm)
                cumu_rel_std.append(data[key+'sig'][maxidx] / baseline_norm)

            # Append value for p_adoption=0 (baseline)
            cumu_rel_mean.append(1.0)
            cumu_rel_std.append(0.0)
            cumu_rel_mean = 1 - np.asarray(cumu_rel_mean)
            cumu_rel_std = np.asarray(cumu_rel_std)

            ax.errorbar(ps_adoption, cumu_rel_mean, yerr=cumu_rel_std, label=titles[i],
                         c=self.color_different_scenarios[i], linestyle='-', elinewidth=0.8, capsize=3.0)

        ax.set_xlim(left=np.min(ps_adoption), right=np.max(ps_adoption))
        ax.set_ylim(ymax=ymax, ymin=0.0)

        ax.set_ylabel(ylabel)
        ax.set_xlabel('Adoption probability')


        if show_legend:
            # legend
            if legend_is_left:
                leg = ax.legend(loc='upper left',
                          bbox_to_anchor=(0.001, 0.999),
                          bbox_transform=ax.transAxes,
                          )
            else:
                leg = ax.legend(loc='upper right',
                          bbox_to_anchor=(0.999, 0.999),
                          bbox_transform=ax.transAxes,
                          )

        subplot_adjust = subplot_adjust or {'bottom': 0.14, 'top': 0.98, 'left': 0.12, 'right': 0.96}
        plt.subplots_adjust(**subplot_adjust)

        plt.savefig('plots/' + filename + '.pdf', format='pdf', facecolor=None,
                    dpi=DPI, bbox_inches='tight')

        if NO_PLOT:
            plt.close()
        return
