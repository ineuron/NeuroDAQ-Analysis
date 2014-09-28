""" Auxiliary analysis functions for 1D data

Data is collected from the currently plotted traces (or selection later)
in a list that is converted into a numpy array. To access attributes of
the trace, such as dt, we also need to match the data to the h5item where
it comes from, so currently plotted items are stored in plotWidget.plotDataItems
(in pgfuncs.py). The items are stored in a list assembled in the same order
as the data list, so the indexes match.
"""

import numpy as np
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
from widgets import h5Item
from util import pgplot

def get_data(browser):
    """ Return the data currently plotted.
    """
    data = []
    for item in browser.ui.dataPlotsWidget.plotDataItems:
        #data.append(browser.ui.workingDataTree.data[item.dataIndex])
        data.append(item.data)
    data = np.array(data) # this will return an error if dts are different (data is not the same len)
    return data


def get_attr(itemsList, attr):
    """ Return a list with the values of attribute attr
    """
    attrList = []
    try:
        for item in itemsList:
            attrList.append(item.attrs[attr])
        return attrList
    except KeyError:
        print attr, 'not found'
    

def get_cursors(plotWidget):
    """ Return the current position of the data cursors
    in X-axis values.
    """
    c1 = plotWidget.cursor1.value()
    c2 = plotWidget.cursor2.value()
    plotWidget.cursor1Pos = c1     # Store positions for re-plotting
    plotWidget.cursor2Pos = c2    
    if c2<c1:        
        temp = c2
        c2 = c1
        c1 = temp
    #return int(c1/plotWidget.dt), int(c2/plotWidget.dt)
    return int(c1), int(c2)


def make_data_copy(browser, plotWidget):
    """ Make a copy of the currently plotted data to work on, 
    in order to keep the original data intact. Add new items
    to the working data tree and plot them, so that plotDataIndex
    is updated.
    """
    plotWidget.clear()
    newPlotDataIndex = []
    data = get_data(browser)
    dataIndex = plotWidget.plotDataIndex   
    item = h5Item(['Baselined_traces'])
    parentWidget = browser.ui.workingDataTree.invisibleRootItem()
    browser.make_nameUnique(parentWidget, item, item.text(0))
    browser.ui.workingDataTree.addTopLevelItem(item)     
    for t in range(len(data)):
        # Add items to tree
        child = h5Item([str(t)])
        browser.make_nameUnique(item, child, child.text(0))
        item.addChild(child)
        child.dataIndex =  len(browser.ui.workingDataTree.data)
        browser.ui.workingDataTree.data.append(browser.ui.workingDataTree.data[dataIndex[t]])   
        
        # Plot data copy
        x = np.arange(0, len(browser.ui.workingDataTree.data[child.dataIndex])*plotWidget.dt, plotWidget.dt)
        y = browser.ui.workingDataTree.data[child.dataIndex]
        plotWidget.plot(x, y, pen=pg.mkPen('#3790CC'))
        newPlotDataIndex.append(child.dataIndex)
    plotWidget.plotDataIndex = newPlotDataIndex
    if browser.ui.actionShowCursors.isChecked(): pgplot.replot_cursors(browser, plotWidget) 


def plot_point(plotWidget, cursor1, xpoint, ypoint, dt):
    """ Plots a single point, with the X coordinate measured from the position
    of cursor 1 (i.e.: cursor 1 X-position = 0). Useful from when processing data
    within the cursor range and needing to plot the results on top of the entire trace.
    """
    x = (xpoint + cursor1) * dt
    plotWidget.plot([x], [ypoint], pen=None, symbol='o', symbolPen='r', symbolBrush=None, symbolSize=7)


def save_results(browser, parentText, results):
    """ Saves data to workingDataTree.data and adds
    corresponding entry in the tree with a parent at 
    root level and children.
    
    'results' is a list with n items ['label', data, attrs]    
    Returns a list with the list indexes of the stored items
    """        
    listIndexes = []
    item = h5Item([parentText])
    parentWidget = browser.ui.workingDataTree.invisibleRootItem()
    browser.make_nameUnique(parentWidget, item, item.text(0))        
    browser.ui.workingDataTree.addTopLevelItem(item)
    for result in results:
        child = h5Item([result[0]])
        browser.make_nameUnique(item, child, child.text(0))
        item.addChild(child)  
        if len(result)>2: child.attrs = result[2]
        child.listIndex =  len(browser.ui.workingDataTree.dataItems)
        listIndexes.append(child.listIndex)
        browser.ui.workingDataTree.dataItems.append(child)
        child.data = result[1]   
    return listIndexes
