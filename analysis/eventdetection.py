""" Event detection functions
"""

import numpy as np
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
from widgets import h5Item
from util import pgplot
import auxfuncs as aux
import smooth

def event_detect(browser):
    """ Temporary event detection function using amplitude
    threshold only. Noise safety is for when coming down from
    peak, go down an extra amount from threshold before starting
    to search for the next event.
    """
    # Read detection options
    threshold = float(browser.ui.toolStackedWidget.eventThreshold.text())
    noiseSafety = float(browser.ui.toolStackedWidget.eventNoiseSafety.text())
    smoothFactor = float(browser.ui.toolStackedWidget.eventSmooth.text())
    c1, c2 = aux.get_cursors(browser.ui.dataPlotsWidget) 

    # Ensure that noise safety has the same sign as the threshold
    noiseSafety = np.sign(threshold) * abs(noiseSafety)

    # Get data currently plotted within the cursors and concatenate in a single sweep
    data = aux.get_data(browser)
    if browser.ui.dataPlotsWidget.cursor1Pos: data = data[:,c1:c2]
    data = data.ravel()

    # Smooth
    data = smooth.smooth(data, window_len=smoothFactor, window='hanning')

    # Run detection   
    comp = lambda a, b: a < b
    eventCounter,i = 0,0
    xOnsets, yOnsets = [], []
    while i<len(data):
        if comp(data[i],threshold):
            xOnsets.append(i)
            yOnsets.append(data[i])
            eventCounter +=1
            while i<len(data) and comp(data[i],(threshold-noiseSafety)):
                i+=1 # skip values if index in bounds AND until the value is below/above threshold again
        else:
            i+=1

    frequency = eventCounter/(len(data)*browser.ui.dataPlotsWidget.dt)*1000   # in Hz
    print eventCounter, 'events detected at', frequency, 'Hz'

    # Store event onsets and peaks in h5 data tree
    item = h5Item(['Event Detection'])
    browser.ui.workingDataTree.addTopLevelItem(item)
    store_array(browser, item, 'trace', np.array(data))
    store_array(browser, item, 'onsets', np.array(xOnsets))
    store_array(browser, item, 'peaks', np.array(yOnsets))
    store_array(browser, item, 'number', np.array(eventCounter))
    store_array(browser, item, 'frequency', np.array(frequency))

    # Store data temporarily in stack widget list for further analysis
    browser.ui.toolStackedWidget.eventData = []
    browser.ui.toolStackedWidget.eventData.append(np.array(data))
    browser.ui.toolStackedWidget.eventData.append(np.array(xOnsets))

    # Plot results
    show_events(browser, data, np.array(xOnsets), np.array(yOnsets))
    #return eventCounter, np.array(xOnsets), np.array(yOnsets)

def event_cut(browser):
    # Get parameters
    data = browser.ui.toolStackedWidget.eventData[0]
    onsets = browser.ui.toolStackedWidget.eventData[1]
    baseline = 2/0.04
    duration = 15/0.04

    # Cut out
    events = []
    for onset in onsets:
        eStart = onset-baseline
        eEnd = onset+duration
        eData = data[eStart:eEnd]
        events.append(eData)

    # Store event waveforms in h5 data tree
    item = h5Item(['Events'])
    browser.ui.workingDataTree.addTopLevelItem(item)
    for e in np.arange(0, len(events)):
        store_array(browser, item, 'event'+str(e), events[e])

def store_array(browser, parent, childName, array):
    child = h5Item([childName]) 
    parent.addChild(child)
    child.dataIndex = len(browser.ui.workingDataTree.data) 
    browser.ui.workingDataTree.data.append(array)


def show_events(browser, data, xOnsets, yOnsets):
    plotWidget = browser.ui.dataPlotsWidget
    plotWidget.clear()
    plotWidget.plot(data)
    plotWidget.plot(xOnsets, yOnsets, pen=None, symbol='o', symbolPen='r', symbolBrush=None, symbolSize=7)

