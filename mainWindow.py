# Setup main interface
#
# Widgets and layouts are created by browser.py, generated using Qt Designer
# and pyuic4 to convert to .py 
#
# T.Branco @ MRC-LMB 2014
# -----------------------------------------------------------------------------
# /home/tiago/Code/py/NeuroDAQanalysis/testData

import sys, os, re, copy

import h5py
import sip
import numpy as np
from PyQt4 import QtGui, QtCore

from gui import Ui_MainWindow
from widgets import h5Item
from util import h5, mplplot, treefun, table, pgplot
from analysis import toolselector

import pyqtgraph as pg

class NeuroDaqWindow(QtGui.QMainWindow):
    """ Assembles the main NeuroDAQ user interface.
    
    Data management:
    
    Data loaded in the Working Data tree are stored in list workingDataTree.data. Each item in 
    the tree had a property item.dataIndex that is the position of the item's data in the list.
    
    To keep track of data plotted in dataPlotsWidget, the indexes of the plotted data are stored 
    in dataPlotsWidget.plotDataIndex
    """
    
    def __init__(self, parent=None):    
        # Initialise and setup UI
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()
        
        # Lists for storing data
        self.db = None
        self.wdb = None
        
        # Current working file and folder for saving)
        self.currentSaveFile = []
        self.currentFolder = []

        # Directory browser
        # -----------------------------------------------------------------------------
        self.ui.dirTree.selectionModel().selectionChanged.connect(self.load_h5_OnSelectionChanged)

        # File data tree
        # -----------------------------------------------------------------------------
        self.ui.fileDataTree.data = []
        self.ui.fileDataTree.currentItemChanged.connect(self.plot_OnSelectionChanged)
        self.ui.fileDataTree.itemSelectionChanged.connect(self.store_Selection)
        self.ui.loadFolderInput.returnPressed.connect(self.update_loadDir)

        # Analysis selection list
        # -----------------------------------------------------------------------------
        self.ui.oneDimToolSelect.selectionModel().selectionChanged.connect(self.select_analysisTool)

        # Working data tree
        # -----------------------------------------------------------------------------
        self.ui.workingDataTree.data = []
        self.ui.actionLoadData.triggered.connect(self.load_h5OnLoadPush)
        self.ui.actionNewFile.triggered.connect(self.create_h5OnNewPush)
        self.ui.actionSaveFile.triggered.connect(self.save_h5OnSavePush)
        self.ui.actionSaveFileAs.triggered.connect(self.save_h5OnSaveAsPush)
        self.connect(self.ui.workingDataTree, QtCore.SIGNAL('dropped'), self.move_itemsAcross)
        self.connect(self.ui.workingDataTree, QtCore.SIGNAL('targetPosition'), self.set_targetPosition)
        self.ui.workingDataTree.propsDt = ''
        self.ui.workingDataTree.propsDescription = ''   

        # Context menu
        self.ui.workingDataTree.customContextMenuRequested.connect(self.open_workingDataTreeMenu)
        self.ui.actionAddRootGroup.triggered.connect(self.add_rootGroupOnMenu)
        self.ui.actionAddChildGroup.triggered.connect(self.add_childGroupOnMenu)
        self.ui.actionRenameTreeItem.triggered.connect(self.rename_itemOnMenu)
        self.ui.actionRemoveTreeItem.triggered.connect(self.remove_itemOnMenu)
        self.ui.actionShowInTable.triggered.connect(self.show_inTableOnMenu)   

        # Properties table        
        # -----------------------------------------------------------------------------        
        self.ui.propsTableWidget.setRowCount(2)
        self.ui.propsTableWidget.setColumnCount(1)
        self.ui.propsTableWidget.horizontalHeader().setVisible(False)
        self.ui.workingDataTree.propsItemDtLabel = QtGui.QTableWidgetItem('dt')
        self.ui.workingDataTree.propsItemDt = QtGui.QTableWidgetItem(self.ui.workingDataTree.propsDt)
        self.ui.workingDataTree.propsItemDescriptionLabel = QtGui.QTableWidgetItem('Description')
        self.ui.workingDataTree.propsItemDescription = QtGui.QTableWidgetItem(self.ui.workingDataTree.propsDescription)                
        self.ui.propsTableWidget.setVerticalHeaderItem(0, self.ui.workingDataTree.propsItemDtLabel)
        self.ui.propsTableWidget.setItem(0,0,self.ui.workingDataTree.propsItemDt)
        self.ui.propsTableWidget.setVerticalHeaderItem(1, self.ui.workingDataTree.propsItemDescriptionLabel)
        self.ui.propsTableWidget.setItem(1,0,self.ui.workingDataTree.propsItemDescription)
        self.ui.propsTableWidget.cellChanged.connect(self.updateTableEntry)        
        
        # Data table tab
        # -----------------------------------------------------------------------------        
 

        # Plots tab
        # ----------------------------------------------------------------------------- 
        self.ui.actionPlotData.triggered.connect(self.plot_selected)
        #self.ui.actionZoomOut.triggered.connect(self.zoom_out)
        self.ui.actionShowCursors.triggered.connect(self.show_cursors)
        self.ui.actionAnalyseData.triggered.connect(self.analyse_data)


    # -----------------------------------------------------------------------------
    # HDF5 file Methods
    # -----------------------------------------------------------------------------
    def load_h5_OnSelectionChanged(self, newSelection, oldSelection):
        """ Load hdf5 file
        """
        if self.db: 
            self.db.close()
            self.db = None
        h5.load_h5(self, self.ui.fileDataTree, push=False)

    def load_h5OnLoadPush(self):
        h5.load_h5(self, self.ui.workingDataTree, push=True)
        
    def create_h5OnNewPush(self):
        h5.create_h5(self, self.ui.workingDataTree)

    def save_h5OnSavePush(self):
        if self.currentSaveFile:
            h5.save_h5(self, self.ui.workingDataTree)
        else: 
            fname, ok = QtGui.QInputDialog.getText(self, 'New file', 'Enter file name:')
            if ok:
                self.currentSaveFile = str(self.model.rootPath()) + '/' + fname + '.hdf5'
                h5.save_h5(self, self.ui.workingDataTree)
        
    def save_h5OnSaveAsPush(self):
        fname, ok = QtGui.QInputDialog.getText(self, 'New file', 'Enter file name:')
        if ok:
            self.currentSaveFile = self.currentFolder + '/' + fname + '.hdf5'      
            h5.save_h5(self, self.ui.workingDataTree)        


    # -----------------------------------------------------------------------------
    # Tree Methods
    # -----------------------------------------------------------------------------    
    def update_loadDir(self):
        treefun.set_loadFolder(self, self.ui.dirTree, self.ui.loadFolderInput.text())
    
    def store_Selection(self):
        """ Store user selected tree items in dragItems list to get them back
        once they have been dropped
        """
        self.dragItems = []    
        for originalIndex in self.ui.fileDataTree.selectedIndexes():
            item = self.ui.workingDataTree.itemFromIndex(QtCore.QModelIndex(originalIndex))
            self.dragItems.append([item.path, item.text(0), item.dataIndex, originalIndex]) 

    def move_itemsAcross(self):
        """ Create new tree items and populate the target tree
        """
        targetItems = []
        for item in self.dragItems:
            i = h5Item([str(item[1])])
            i.path = item[0]
            i.dataIndex = item[2]
            i.originalIndex = item[3]
            targetItems.append(i)             
        parentIndex = self.ui.workingDataTree.indexFromItem(self.dragTargetParent)
        for row in np.arange(0, len(self.dragItems)):
            index = self.ui.workingDataTree.model().index(self.dragTargetRow+row, 0, parentIndex)        
            temp_item = self.ui.workingDataTree.itemFromIndex(QtCore.QModelIndex(index))
            sip.delete(temp_item)        
            if parentIndex.isValid():
                self.dragTargetParent.insertChild(index.row(), targetItems[row])
                originalParentWidget = self.ui.fileDataTree.itemFromIndex(QtCore.QModelIndex(targetItems[row].originalIndex))
                h5.populate_h5dragItems(self, originalParentWidget, targetItems[row])
            else:
                self.ui.workingDataTree.insertTopLevelItem(index.row(), targetItems[row])     
                originalParentWidget = self.ui.fileDataTree.itemFromIndex(QtCore.QModelIndex(targetItems[row].originalIndex))
                h5.populate_h5dragItems(self, originalParentWidget, targetItems[row])
                
    def set_targetPosition(self, parent, row):
        self.dragTargetParent = parent
        self.dragTargetRow = row

    def open_workingDataTreeMenu(self, position):
        """ Context menu for working data tree
        """
        self.workingDataTreeMenu = QtGui.QMenu()
        self.workingDataTreeMenu.addAction(self.ui.actionAddRootGroup)
        self.workingDataTreeMenu.addAction(self.ui.actionAddChildGroup)
        self.workingDataTreeMenu.addAction(self.ui.actionAddDataset)
        self.workingDataTreeMenu.addAction(self.ui.actionRenameTreeItem)
        self.workingDataTreeMenu.addAction(self.ui.actionRemoveTreeItem)
        self.workingDataTreeMenu.addAction(self.ui.actionShowInTable)

        if len(self.ui.workingDataTree.selectedItems())==0: 
            self.ui.actionAddChildGroup.setDisabled(True)
            self.ui.actionRenameTreeItem.setDisabled(True)
        else:
            self.ui.actionAddChildGroup.setDisabled(False)
            self.ui.actionRenameTreeItem.setDisabled(False)            
        self.workingDataTreeMenu.exec_(self.ui.workingDataTree.viewport().mapToGlobal(position))

    def add_rootGroupOnMenu(self):
        treefun.add_treeGroup(self, self.ui.workingDataTree, 'root')
       
    def add_childGroupOnMenu(self):
        treefun.add_treeGroup(self, self.ui.workingDataTree, 'child')
    
    def rename_itemOnMenu(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Rename item', 'Enter new name:')
        if ok: treefun.rename_treeItem(self, self.ui.workingDataTree, str(text))

    def remove_itemOnMenu(self):
        treefun.remove_treeItem(self, self.ui.workingDataTree)

    def show_inTableOnMenu(self):
        table.clear_table(self)
        table.put_dataOnTable(self)

    # -----------------------------------------------------------------------------
    # Analysis Methods
    # -----------------------------------------------------------------------------
    def select_analysisTool(self):
        index = self.ui.oneDimToolSelect.selectedIndexes()[0]
        self.ui.toolStackedWidget.setCurrentIndex(index.row())
        return index

    def analyse_data(self):
        index = self.select_analysisTool()
        if index:
            tool = index.data().toString()
            toolselector.toolselector(self, tool)

    # -----------------------------------------------------------------------------
    # Properties Methods
    # -----------------------------------------------------------------------------
    def updateTableEntry(self, row, col):
        if row==0: self.ui.workingDataTree.propsDt = self.ui.propsTableWidget.item(row, col).text() 
        if row==1: self.ui.workingDataTree.propsDescription = self.ui.propsTableWidget.item(row, col).text() 

    # -----------------------------------------------------------------------------
    # Table Methods
    # -----------------------------------------------------------------------------

    def show_inTableOnMenu(self):
        #self.ui.dataTableWidget.setData({'x': [1,2,3], 'y': [4,5,6]})#np.random.random(100))
        table.put_dataOnTable(self)

    # -----------------------------------------------------------------------------
    # Plotting Methods
    # -----------------------------------------------------------------------------
    def plot_OnSelectionChanged(self, current, previous):
        if current:
            if 'dataset' in str(self.db[current.path]):
                pgplot.plot_singleData(self, self.ui.singlePlotWidget, self.db[current.path][:])    

    def plot_selected(self):
        pgplot.plot_multipleData(self, self.ui.dataPlotsWidget)   
    
    def zoom_out(self):
        pgplot.zoom_out(self, self.ui.dataPlotsWidget)

    def show_cursors(self):
        if self.ui.actionShowCursors.isChecked():
            pgplot.show_cursors(self, self.ui.dataPlotsWidget)
        else:
            pgplot.hide_cursors(self, self.ui.dataPlotsWidget)
        

def main():    
    defaultFont = QtGui.QFont('Ubuntu', 8) 
    app = QtGui.QApplication(sys.argv)
    app.setFont(defaultFont)
    c = NeuroDaqWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 




