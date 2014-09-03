import platform
from PyQt4 import QtGui, QtCore


class FileBrowserWidget(QtGui.QTreeView):

    """ Reimplement QTreeWidget Class 
    
    Set Model to QFileSystemModel.
    Allows setting size hint and Home Folder
           
    TabWidget(width, height, [homeFolder=None])
    """

    def __init__(self, width, height, homeFolder=None):
        QtGui.QTreeView.__init__(self)
        self._width = width
        self._height = height 
        self.model = QtGui.QFileSystemModel()
        self.setModel(self.model)

        # Set home folder and file filters
        if not homeFolder: 
            if platform.system()=='Darwin':
                homeFolder = '/Users/'
            elif platform.system()=='Linux':
                homeFolder = '/home/'        
        self.model.setRootPath(QtCore.QDir.absolutePath(QtCore.QDir(homeFolder)))
        self.setRootIndex(self.model.index(QtCore.QDir.absolutePath(QtCore.QDir(homeFolder))))                
        self.model.setNameFilters(['*.hdf5'])
 
        # Hide some default columns
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)   
        
    def sizeHint(self):
        return QtCore.QSize(self._width, self._height)


