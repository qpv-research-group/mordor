""" This module includes a colection of functions that simplify the tasks of creating, updating and changing the data
on a given subfigure.
"""

__author__ = 'diego'


def update(subplot, ydata, xdata=None, idx=-1):
    """ Updates the x and y data in the plot idx. Afterwards, it changes the scale to fit all the data.

    :param subplot: Subplot that want to be updated
    :param ydata: The new y-data. It must be the same that the corresponding x-data
    :param xdata: The new x-data. By default, it uses the existing x-data
    :param idx: The index of the plot to be updated. By default, we update the last plot
    :return: 0 if OK
    """

    # Check if there is anything to update
    lplot = len(subplot.lines)
    assert lplot > 0, '*** Error udating the plot: There is no plot to update.'

    # Check if the lengths of the x and y data are compatible
    ly = len(ydata)
    if xdata is not None:
        lx = len(xdata)
    else:
        lx = len(subplot.lines[idx].get_xdata())
    assert ly == lx, '*** Error udating the plot: x and y data must have the same lenght. x: {0}, y: {1}'.format(
        lx, ly)

    # So far, so good. We update the plot and the scale
    subplot.lines[idx].set_ydata(ydata)
    update_scale(subplot, ydata, axis='y')

    if xdata is not None:
        subplot.lines[idx].set_xdata(xdata)
        update_scale(subplot, xdata, axis='x')

    return 0

def update_labels(subplot, xlabel, ylabel):
    subplot.set_xlabel(xlabel)
    subplot.set_ylabel(ylabel)
	
def update_yscales(subplot, Y_scale):
    try:
        subplot.set_yscale(Y_scale)
    except Exception:
        print('Error in axis scale argument')
        
def update_xscales(subplot, X_scale):
    try:
        subplot.set_xscale(X_scale)
    except Exception:
        print('Error in axis scale argument')
    

def clear(subplot, xtitle=None, xticks='on', ytitle=None, yticks='on'):
    """ Clears the subplot of any plot, changes the axis labels and ticks, if necessary, and reset the scale to the default values.

    :param subplot: Subplot that want to be cleared
    :param xtitle: The new title for the x axes. Default=None (unchanged)
    :param xticks: Activates or deactivates the ticks in the x axis. Default='on'
    :param ytitle: The new title for the y axes. Default=None (unchanged)
    :param yticks: Activates or deactivates the ticks in the y axis. Default='on'
    :return: 0 if OK
    """

    n = len(subplot.lines)
    for i in range(n):
        subplot.lines.remove(subplot.lines[0])

    subplot.tick_params(axis='x', labelbottom=xticks)
    subplot.tick_params(axis='y', labelbottom=yticks)

    if xtitle is not None:
        subplot.set_xlabel(xtitle)
    if ytitle is not None:
        subplot.set_ylabel(ytitle)

    return 0


def update_scale(subplot, data, axis='y'):
    """ Updates the axis of a subplot to certain max/min values. Special care has to be taken in the case of log-scale
    to ensure that the limits are always possitive values.

    :param subplot: The subplot to be updated
    :param data: 1D array. The data used to calculate the scale
    :param axis: 'x' or 'y'. The axis whose scale is to be updated. Default='y'
    :return: Return 0 if OK.
    """
    assert axis == 'x' or axis == 'y', '*** Error updating the scale: Axis option must be \'x\' or \'y\' '

    if axis=='y':
        scale_type = subplot.get_yaxis().get_scale()

        if scale_type == 'log':
            min_data = min(data[data > 0])
        else:
            min_data = min(data) - 0.05*abs(min(data))

        max_data = max(data) + 0.05*abs(max(data))
        if abs(min_data)+abs(max_data) == 0:
            min_data = -1
            max_data = 1

        if scale_type == 'log' and min_data <= 0:
            min_data = max_data/10

        subplot.set_ybound(lower=min_data, upper=max_data)
    else:
        min_data = data[0]
        max_data = data[-1]
        subplot.set_xbound(lower=min_data, upper=max_data)

    return 0


def plot_all(subplot, data, idx=(0, 1), color=None):
    """ Plots all data in the given subplot using the columns indicated in idx.

    :param subplot: The subplot where data is to be ploted
    :param data: A list of rank-2 arrays. The data to be plotted.
    :param idx: A tuple with the indices of the columns XY to be plotted. Default=(0,1)
    :param color: String. A standard color or None. Default=None.
    :return: Return 0 if OK.
    """

    # Check if there is anithing to plot
    n = len(data)
    # assert n > 0, '*** Error plotting all: There is nothing to plot.'
    if n == 0:
        return 1

    if color is None:
        for i in range(n):
            subplot.plot(data[i][:, idx[0]], data[i][:, idx[1]])
    else:
        for i in range(n):
            subplot.plot(data[i][:, idx[0]], data[i][:, idx[1]], color=color)

    update_scale(subplot, data[-1][:, idx[0]], axis='x')
    update_scale(subplot, data[-1][:, idx[1]], axis='y')

    return 0