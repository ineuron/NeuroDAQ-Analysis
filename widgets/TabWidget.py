from PyQt4 import QtGui, QtCore


class TabWidget(QtGui.QTabWidget):

    """ Reimplement QTabWidget Class to allow setting a size hint.  
        TabWidget(width, height)
    """

    def __init__(self, width, height):
        QtGui.QTabWidget.__init__(self)
        self._width = width
        self._height = height
        
    def sizeHint(self):
        return QtCore.QSize(self._width, self._height)


